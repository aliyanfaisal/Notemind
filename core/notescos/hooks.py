"""Claude Code hook handlers. They must be fast and must never break a session."""

from __future__ import annotations

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .brief import build_brief, format_banner
from .store import NoteStore, default_home

WELCOME = """📌 Notemind is ready.
  /notemind:note-add <text>   save a note (dates in your sentence are understood)
  /notemind:note-today        what needs your attention
  /notemind:note-help         all commands"""

BANNER_HORIZON_DAYS = 2  # session banner covers overdue, today and the next 2 days


def session_start(stdin_text: str, now: datetime, home: Optional[Path] = None) -> Optional[Dict]:
    """Build the SessionStart hook output, or None when there is nothing to say."""
    home = home or default_home()
    try:
        source = json.loads(stdin_text or "{}").get("source", "startup")
    except (ValueError, AttributeError):
        source = "startup"
    if source == "compact":  # context was just trimmed mid-session; don't repeat the banner
        return None

    parts = []
    welcomed = home / "welcomed"
    first_run = not welcomed.exists()
    if first_run:
        parts.append(WELCOME)
    with NoteStore(home / "notes.db") as store:
        brief = build_brief(store.list(), now, BANNER_HORIZON_DAYS, skip_silent=True)
    banner = format_banner(brief, now)
    if banner:
        parts.append(banner)
    if not parts:
        return None
    if first_run:
        home.mkdir(parents=True, exist_ok=True)
        welcomed.write_text(now.isoformat(timespec="seconds"))

    text = "\n\n".join(parts)
    return {
        "systemMessage": text,  # shown to the user
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                "Notemind summary of the user's open notes. Mention it only "
                "if relevant; the user has already seen it.\n" + text
            ),
        },
    }


def log_error(home: Path) -> None:
    """Record a hook failure for later debugging without disturbing the session."""
    try:
        home.mkdir(parents=True, exist_ok=True)
        with open(home / "log", "a") as handle:
            handle.write(f"{datetime.now().isoformat(timespec='seconds')} session-start\n")
            handle.write(traceback.format_exc() + "\n")
    except OSError:
        pass
