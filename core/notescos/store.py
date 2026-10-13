"""SQLite storage for notes. Standard library only, no network."""

from __future__ import annotations

import json
import os
import re
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
    # Full-text search over the words a person would ask about. Optional: see _migrate.
    """
    CREATE VIRTUAL TABLE notes_fts USING fts5(
        text, person, project, tags, content='notes', content_rowid='id');
    INSERT INTO notes_fts (rowid, text, person, project, tags)
        SELECT id, text, person, project, tags FROM notes;
    CREATE TRIGGER notes_fts_insert AFTER INSERT ON notes BEGIN
        INSERT INTO notes_fts (rowid, text, person, project, tags)
        VALUES (new.id, new.text, new.person, new.project, new.tags);
    END;
    CREATE TRIGGER notes_fts_delete AFTER DELETE ON notes BEGIN
        INSERT INTO notes_fts (notes_fts, rowid, text, person, project, tags)
        VALUES ('delete', old.id, old.text, old.person, old.project, old.tags);
    END;
    CREATE TRIGGER notes_fts_update AFTER UPDATE OF text, person, project, tags ON notes BEGIN
        INSERT INTO notes_fts (notes_fts, rowid, text, person, project, tags)
        VALUES ('delete', old.id, old.text, old.person, old.project, old.tags);
        INSERT INTO notes_fts (rowid, text, person, project, tags)
        VALUES (new.id, new.text, new.person, new.project, new.tags);
    END;
    """,
]
FTS_MIGRATION = 2  # the number (1-based) of the entry above

# Words that say nothing about which note is meant.
STOP_WORDS = frozenset(
    "a an and are about all any did do does for from had has have how i in is it me my "
    "of on or the to was what when where which who whom why with you your".split()
)


class NoteError(Exception):
    """A user-facing problem (bad input, unknown note)."""


class DateNotUnderstood(NoteError):
    """The built-in rules cannot read this date with confidence; Claude should resolve it."""


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
            try:
                with self.conn:
                    self.conn.executescript("BEGIN;" + MIGRATIONS[number])
                    self.conn.execute(f"PRAGMA user_version = {number + 1}")
            except sqlite3.OperationalError:
                # Some Python builds ship SQLite without FTS5. Search then falls back to
                # plain matching, so this one migration is allowed to be skipped.
                if number + 1 != FTS_MIGRATION:
                    raise
                self.conn.rollback()
                self.conn.execute(f"PRAGMA user_version = {number + 1}")
        self.has_fts = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'notes_fts'").fetchone() is not None

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
        due_from: Optional[str] = None,
        due_to: Optional[str] = None,
    ) -> List[Dict]:
        """Notes ordered by due date (undated last), then oldest first.

        status "active" means open plus snoozed. due_from / due_to are inclusive YYYY-MM-DD days; notes without a due date
        never match when either is given.
        """
        clauses, params = [], []
        if status == "active":  # everything not finished: open and snoozed
            clauses.append("status IN ('open','snoozed')")
            status = None
        for bound, op in ((due_from, ">="), (due_to, "<=")):
            if bound is not None:
                clauses.append(f"substr(due_at, 1, 10) {op} ?")
                params.append(normalize_due(bound)[:10])
        for column, value in (("status", status), ("type", type), ("project", project)):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.conn.execute(
            f"SELECT * FROM notes {where} ORDER BY due_at IS NULL, due_at, id", params
        ).fetchall()
        return [self._row(r) for r in rows]

    def search(self, question: str, *, limit: int = 10, include_done: bool = True) -> List[Dict]:
        """Notes that match the words of a question, best match first.

        Every word counts on its own (any of them may match) and may be the start of a
        longer word, so "invoic" finds "invoice". Each result has a "rank" (lower is better).
        """
        words = [w[:-1] if len(w) > 3 and w.endswith("s") else w  # "invoices" -> "invoice"
                 for w in re.findall(r"\w+", question.lower())
                 if w not in STOP_WORDS and len(w) > 1]
        if not words:
            return []
        status = "" if include_done else "AND n.status != 'done'"
        if self.has_fts:
            match = " OR ".join(f'"{w}"*' for w in words)
            rows = self.conn.execute(
                f"""SELECT n.*, bm25(notes_fts) AS rank FROM notes_fts
                    JOIN notes n ON n.id = notes_fts.rowid
                    WHERE notes_fts MATCH ? {status}
                    ORDER BY rank, n.id LIMIT ?""", (match, limit)).fetchall()
        else:
            haystack = "lower(n.text || ' ' || coalesce(n.person,'') || ' ' || coalesce(n.project,'')"
            haystack += " || ' ' || n.tags)"
            hits = " + ".join(f"({haystack} LIKE ?)" for _ in words)
            rows = self.conn.execute(
                f"""SELECT n.*, -({hits}) AS rank FROM notes n
                    WHERE ({hits}) > 0 {status}
                    ORDER BY rank, n.id LIMIT ?""",
                [f"%{w}%" for w in words] * 2 + [limit]).fetchall()
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

    # Fields note-edit may change. None clears due, person and project.
    _EDITABLE = ("text", "type", "due", "priority", "alert_level", "person", "project", "tags",
                 "confirmed")

    def update(self, note_id: int, **changes) -> Dict:
        """Change the given fields of a note; fields not passed are left alone."""
        self.get(note_id)
        unknown = set(changes) - set(self._EDITABLE)
        if unknown:
            raise NoteError(f"Cannot edit: {', '.join(sorted(unknown))}.")
        columns: Dict[str, object] = {}
        if "text" in changes:
            text = (changes["text"] or "").strip()
            if not text:
                raise NoteError("A note needs some text.")
            columns["text"] = text
        if "type" in changes:
            if changes["type"] not in NOTE_TYPES:
                raise NoteError(f"Unknown type {changes['type']!r}. Choose from: {', '.join(NOTE_TYPES)}.")
            columns["type"] = changes["type"]
        if "due" in changes:
            columns["due_at"] = normalize_due(changes["due"]) if changes["due"] else None
            columns["confirmed"] = 1  # the user just chose this date
        if "confirmed" in changes:
            columns["confirmed"] = int(bool(changes["confirmed"]))
        if "priority" in changes:
            if changes["priority"] not in (0, 1, 2, 3):
                raise NoteError("Priority must be 0 (none), 1, 2 or 3.")
            columns["priority"] = changes["priority"]
        if "alert_level" in changes:
            if changes["alert_level"] not in ALERT_LEVELS:
                raise NoteError(
                    f"Unknown alert level {changes['alert_level']!r}. Choose from: {', '.join(ALERT_LEVELS)}.")
            columns["alert_level"] = changes["alert_level"]
        for name in ("person", "project"):
            if name in changes:
                columns[name] = (changes[name] or "").strip() or None
        if "tags" in changes:
            columns["tags"] = json.dumps(changes["tags"] or [])
        if not columns:
            return self.get(note_id)
        columns["updated_at"] = self._clock()
        assignments = ", ".join(f"{name} = ?" for name in columns)
        with self.conn:
            self.conn.execute(
                f"UPDATE notes SET {assignments} WHERE id = ?", [*columns.values(), note_id])
        return self.get(note_id)

    def snooze(self, note_id: int, until: Optional[str]) -> Dict:
        """Hide an open note until a local date/time; until=None brings it back now."""
        note = self.get(note_id)
        if note["status"] == "done":
            raise NoteError(f"Note #{note_id} is already done.")
        when = normalize_due(until) if until else None
        with self.conn:
            self.conn.execute(
                "UPDATE notes SET status = ?, snoozed_until = ?, updated_at = ? WHERE id = ?",
                ("snoozed" if when else "open", when, self._clock(), note_id),
            )
        return self.get(note_id)

    def wake(self, now: datetime) -> int:
        """Bring back snoozed notes whose time has come. Returns how many woke up."""
        stamp = now.isoformat(timespec="minutes")  # a date-only snooze wakes at 00:00
        with self.conn:
            cur = self.conn.execute(
                "UPDATE notes SET status = 'open', snoozed_until = NULL, updated_at = ? "
                "WHERE status = 'snoozed' AND snoozed_until <= ?",
                (self._clock(), stamp),
            )
        return cur.rowcount
