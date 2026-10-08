"""Claude Code hook handlers. They must be fast and must never break a session."""

from __future__ import annotations

import json
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .brief import build_brief, format_banner, format_banner_markdown
from .store import NoteStore, default_home

WELCOME = """📌 Notemind is ready.
  /notemind:note-add <text>   save a note (dates in your sentence are understood)
  /notemind:note-today        what needs your attention
  /notemind:note-help         all commands"""

# Clients that run hooks but do not display a hook's systemMessage to the user.
HIDES_HOOK_MESSAGES = {"claude-desktop"}

BANNER_HORIZON_DAYS = 2
REPEAT_AFTER_HOURS = 4  # in the app, do not repeat an unchanged banner within this time  # session banner covers overdue, today and the next 2 days


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
    hides = os.environ.get("CLAUDE_CODE_ENTRYPOINT") in HIDES_HOOK_MESSAGES
    banner = format_banner_markdown(brief, now) if hides else format_banner(brief, now)
    if banner and hides and _shown_recently(home, brief, now):
        banner = ""  # the user already saw this exact list a moment ago
    if banner:
        parts.append(banner)
    if not parts:
        return None
    if first_run:
        home.mkdir(parents=True, exist_ok=True)
        welcomed.write_text(now.isoformat(timespec="seconds"))

    text = "\n\n".join(parts)
    if hides:
        instruction = (
            "Notemind summary of the user's open notes. This app does not show hook "
            "messages, so the user has NOT seen it. Start your first reply with the "
            "block below, copied exactly (it is markdown, keep the formatting), "
            "then answer the user's request normally. Do not add commentary about it.\n"
        )
    else:
        instruction = (
            "Notemind summary of the user's open notes. Mention it only "
            "if relevant; the user has already seen it.\n"
        )
    return {
        "systemMessage": text,  # shown to the user by clients that display it
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": instruction + text,
        },
    }


def _shown_recently(home: Path, brief, now: datetime) -> bool:
    """True if this same set of urgent notes was announced less than REPEAT_AFTER_HOURS ago."""
    ids = sorted(n["id"] for n in brief.overdue + brief.due_today)
    state = home / "last_banner.json"
    try:
        last = json.loads(state.read_text())
        same = last.get("ids") == ids
        fresh = (now - datetime.fromisoformat(last["at"])).total_seconds() < REPEAT_AFTER_HOURS * 3600
        if same and fresh:
            return True
    except (OSError, ValueError, KeyError):
        pass
    try:
        home.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps({"ids": ids, "at": now.isoformat(timespec="seconds")}))
    except OSError:
        pass
    return False


def log_error(home: Path) -> None:
    """Record a hook failure for later debugging without disturbing the session."""
    try:
        home.mkdir(parents=True, exist_ok=True)
        with open(home / "log", "a") as handle:
            handle.write(f"{datetime.now().isoformat(timespec='seconds')} session-start\n")
            handle.write(traceback.format_exc() + "\n")
    except OSError:
        pass
