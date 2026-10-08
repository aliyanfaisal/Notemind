"""SQLite storage for notes. Standard library only, no network."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

NOTE_TYPES = (
    "task",
    "followup",
    "waiting_on",
    "money_owed",  # reserved: exposed in M3
    "money_due",  # reserved: exposed in M3
    "decision",
    "idea",
    "reference",
)
STATUSES = ("open", "done", "snoozed")
ALERT_LEVELS = ("normal", "urgent", "silent")

# Each entry upgrades the schema by one version. Never edit a shipped entry;
# append a new one.
MIGRATIONS = [
    """
    CREATE TABLE notes (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        text          TEXT NOT NULL CHECK (length(trim(text)) > 0),
        type          TEXT NOT NULL DEFAULT 'task'
                      CHECK (type IN ('task','followup','waiting_on','money_owed',
                                      'money_due','decision','idea','reference')),
        status        TEXT NOT NULL DEFAULT 'open'
                      CHECK (status IN ('open','done','snoozed')),
        due_at        TEXT,
        remind_at     TEXT,
        snoozed_until TEXT,
        priority      INTEGER NOT NULL DEFAULT 0 CHECK (priority BETWEEN 0 AND 3),
        alert_level   TEXT NOT NULL DEFAULT 'normal'
                      CHECK (alert_level IN ('normal','urgent','silent')),
        person        TEXT,
        amount        REAL,
        currency      TEXT,
        project       TEXT,
        branch        TEXT,
        tags          TEXT NOT NULL DEFAULT '[]',
        source        TEXT NOT NULL DEFAULT 'manual',
        source_ref    TEXT,
        confirmed     INTEGER NOT NULL DEFAULT 1 CHECK (confirmed IN (0,1)),
        created_at    TEXT NOT NULL,
        updated_at    TEXT NOT NULL,
        done_at       TEXT
    );
    CREATE INDEX idx_notes_status ON notes (status);
    CREATE INDEX idx_notes_due_at ON notes (due_at);
    CREATE INDEX idx_notes_project ON notes (project);
    """,
]


class NoteError(Exception):
    """A user-facing problem (bad input, unknown note)."""


def default_home() -> Path:
    """Data directory: $NOTESCOS_HOME or ~/.notescos."""
    override = os.environ.get("NOTESCOS_HOME")
    return Path(override).expanduser() if override else Path.home() / ".notescos"


def normalize_due(value: str) -> str:
    """Validate an ISO date or datetime (YYYY-MM-DD or YYYY-MM-DDTHH:MM).

    Due times are local wall-clock intent, so they are stored without a zone.
    Natural-language dates arrive in M1.
    """
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise NoteError(
            f"Could not read date {value!r}. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM."
        ) from None
    if parsed.tzinfo is not None:
        raise NoteError("Due dates are local time; leave out the timezone offset.")
    return text if len(text) == 10 else parsed.isoformat(timespec="minutes")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class NoteStore:
    def __init__(self, path: Optional[Path] = None, clock: Callable[[], str] = _utc_now):
        self.path = Path(path) if path else default_home() / "notes.db"
        self._clock = clock
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "NoteStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _migrate(self) -> None:
        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        if version > len(MIGRATIONS):
            raise NoteError(
                f"{self.path} was made by a newer notescos (schema {version}). "
                "Upgrade notescos."
            )
        for number in range(version, len(MIGRATIONS)):
            with self.conn:
                self.conn.executescript("BEGIN;" + MIGRATIONS[number])
                self.conn.execute(f"PRAGMA user_version = {number + 1}")

    @staticmethod
    def _row(row: sqlite3.Row) -> Dict:
        note = dict(row)
        note["tags"] = json.loads(note["tags"])
        return note

    def add(
        self,
        text: str,
        *,
        type: str = "task",
        due: Optional[str] = None,
        priority: int = 0,
        alert_level: str = "normal",
        person: Optional[str] = None,
        project: Optional[str] = None,
        branch: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source: str = "manual",
        source_ref: Optional[str] = None,
        confirmed: bool = True,
    ) -> Dict:
        text = (text or "").strip()
        if not text:
            raise NoteError("A note needs some text.")
        if type not in NOTE_TYPES:
            raise NoteError(f"Unknown type {type!r}. Choose from: {', '.join(NOTE_TYPES)}.")
        if alert_level not in ALERT_LEVELS:
            raise NoteError(
                f"Unknown alert level {alert_level!r}. Choose from: {', '.join(ALERT_LEVELS)}."
            )
        if priority not in (0, 1, 2, 3):
            raise NoteError("Priority must be 0 (none), 1, 2 or 3.")
        due_at = normalize_due(due) if due else None
        now = self._clock()
        with self.conn:
            cur = self.conn.execute(
                """INSERT INTO notes (text, type, due_at, priority, alert_level, person,
                       project, branch, tags, source, source_ref, confirmed,
                       created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (text, type, due_at, priority, alert_level, person, project, branch,
                 json.dumps(tags or []), source, source_ref, int(confirmed), now, now),
            )
        return self.get(cur.lastrowid)

    def get(self, note_id: int) -> Dict:
        row = self.conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        if row is None:
            raise NoteError(f"No note with id {note_id}.")
        return self._row(row)

    def list(
        self,
        *,
        status: Optional[str] = "open",
        type: Optional[str] = None,
        project: Optional[str] = None,
    ) -> List[Dict]:
        """Notes ordered by due date (undated last), then oldest first."""
        clauses, params = [], []
        for column, value in (("status", status), ("type", type), ("project", project)):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.conn.execute(
            f"SELECT * FROM notes {where} ORDER BY due_at IS NULL, due_at, id", params
        ).fetchall()
        return [self._row(r) for r in rows]

    def done(self, note_id: int) -> Dict:
        """Mark a note done. Safe to repeat."""
        note = self.get(note_id)
        if note["status"] == "done":
            return note
        now = self._clock()
        with self.conn:
            self.conn.execute(
                "UPDATE notes SET status='done', done_at=?, updated_at=? WHERE id=?",
                (now, now, note_id),
            )
        return self.get(note_id)
