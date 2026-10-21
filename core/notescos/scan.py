"""Read your own typed messages from Claude Code session transcripts, so Claude can propose notes.

Rules only: this module never decides what is a commitment and never saves anything. It
returns the messages you typed since the last review, with sensitive data already masked.
Scanning is opt-in per project (see settings.sync_projects), and only text you typed is read,
never Claude's replies or tool output. Nothing leaves your machine from here.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from .redact import redact

MAX_TEXT = 500  # characters kept per message
STATE_FILE = "sync_state.json"  # {transcript file name: lines already reviewed}
PENDING_FILE = "sync_pending.json"  # where the latest scan stopped, until the user reviews it


def transcripts_home() -> Path:
    """Where Claude Code keeps transcripts: $NOTESCOS_TRANSCRIPTS, else <claude config>/projects."""
    override = os.environ.get("NOTESCOS_TRANSCRIPTS")
    if override:
        return Path(override).expanduser()
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude").expanduser() / "projects"


def project_dir(cwd: str) -> Path:
    """Claude Code names a project's folder after its path, every non-alphanumeric turned to '-'."""
    return transcripts_home() / re.sub(r"[^A-Za-z0-9]", "-", cwd)


def _typed_text(entry: Dict) -> Optional[str]:
    """The text you typed in this transcript line, or None for anything else."""
    if entry.get("type") != "user" or entry.get("isSidechain"):
        return None
    if (entry.get("origin") or {}).get("kind", "human") != "human":
        return None
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, list):  # tool results are blocks of another type and drop out here
        content = " ".join(b.get("text", "") for b in content
                           if isinstance(b, dict) and b.get("type") == "text")
    if not isinstance(content, str):
        return None
    text = " ".join(content.split())
    # Slash commands, #note captures and system wrappers are not free-form commitments.
    if not text or text[0] in "/<#":
        return None
    return text


def load_state(home: Path) -> Dict[str, int]:
    try:
        data = json.loads((home / STATE_FILE).read_text())
        return {k: int(v) for k, v in data.items()} if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def scan(cwd: str, home: Path, limit: int = 40) -> Dict:
    """Unreviewed typed messages for this project, newest last, with secrets masked.

    Returns {"messages": [...], "masked": n, "cursors": {file: line_count}}. Pass the cursors to
    mark_reviewed() once the user has gone through the messages. Reading never moves them.
    """
    state = load_state(home)
    messages: List[Dict] = []
    cursors: Dict[str, int] = {}
    masked = 0
    folder = project_dir(cwd)
    files = sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime) if folder.is_dir() else []
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        cursors[path.name] = len(lines)
        for number, raw in enumerate(lines[state.get(path.name, 0):], start=state.get(path.name, 0) + 1):
            try:
                entry = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(entry, dict):
                continue
            text = _typed_text(entry)
            if text is None:
                continue
            clean, found = redact(text[:MAX_TEXT])
            masked += len(found)
            messages.append({
                "session": entry.get("sessionId") or path.stem,
                "line": number,
                "at": entry.get("timestamp"),
                "branch": entry.get("gitBranch"),
                "text": clean,
            })
    older = max(0, len(messages) - limit) if limit else 0
    messages = messages[-limit:] if limit else messages
    return {"messages": messages, "masked": masked, "older_skipped": older, "cursors": cursors}


def hold_for_review(home: Path, cursors: Dict[str, int]) -> None:
    """Remember where this scan stopped. It only takes effect when mark_reviewed() is called."""
    home.mkdir(parents=True, exist_ok=True)
    (home / PENDING_FILE).write_text(json.dumps(cursors, indent=2) + "\n")


def mark_reviewed(home: Path) -> int:
    """Move the cursors to where the last scan stopped. Returns how many transcripts moved."""
    try:
        pending = {k: int(v) for k, v in json.loads((home / PENDING_FILE).read_text()).items()}
    except (OSError, ValueError, TypeError, AttributeError):
        return 0
    state = load_state(home)
    state.update(pending)
    (home / STATE_FILE).write_text(json.dumps(state, indent=2) + "\n")
    (home / PENDING_FILE).unlink()
    return len(pending)
