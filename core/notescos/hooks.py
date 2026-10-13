"""Claude Code hook handlers. They must be fast and must never break a session."""

from __future__ import annotations

import io
import json
import os
import re
import shlex
import traceback
from contextlib import redirect_stderr
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from . import settings as user_settings
from .banner import build_banner
from .brief import build_brief, format_saved
from .parse import ambiguity, needs_claude, parse_due
from .redact import find_sensitive, redact_notes
from .store import NoteStore, default_home

WELCOME = """📌 Notemind is ready.
  /notemind:note-add <text>   save a note (dates in your sentence are understood)
  /notemind:note-today        what needs your attention
  /notemind:note-help         all commands"""

# Clients that run hooks but do not display a hook's systemMessage to the user.
HIDES_HOOK_MESSAGES = {"claude-desktop"}

REPEAT_AFTER_HOURS = 4  # in the app, do not repeat an unchanged banner within this time


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
        store.wake(now)
        notes = store.list()
    level = user_settings.load(home)["alert_level"]
    # What Claude is given has sensitive data masked; the user's own banner does not.
    safe_notes = redact_notes(notes)[0]
    hides = os.environ.get("CLAUDE_CODE_ENTRYPOINT") in HIDES_HOOK_MESSAGES
    # The app has Claude show the banner to the user, so it must be the masked one there.
    banner = build_banner(safe_notes if hides else notes, now, level, markdown=hides)
    safe_banner = build_banner(safe_notes, now, level, markdown=hides)
    if banner and hides and _shown_recently(home, build_brief(notes, now), now):
        banner = ""  # the user already saw this exact list a moment ago
    if banner:
        parts.append(banner)
    if not parts:
        return None
    safe_parts = [p if p is not banner else safe_banner for p in parts]
    if first_run:
        home.mkdir(parents=True, exist_ok=True)
        welcomed.write_text(now.isoformat(timespec="seconds"))

    text = "\n\n".join(parts)
    safe_text = "\n\n".join(safe_parts)
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
            "additionalContext": instruction + safe_text,
        },
    }


# `#note call Sara friday 3pm`: quick capture that never reaches Claude.
INLINE_NOTE_RE = re.compile(r"^\s*#note\s+(.+)$", re.DOTALL | re.IGNORECASE)
COMMAND_RE = re.compile(
    r"^\s*/(?:notemind:)?(note-add|note-today|note-list|note-done|note-edit|note-snooze"
    r"|note-top|note-check|note-settings)(?:\s+(.*))?$",
    re.DOTALL | re.IGNORECASE,
)
# Commands whose output depends only on the notes, so they never need Claude.
LOCAL_COMMANDS = {
    "note-today": "today", "note-list": "list", "note-done": "done",
    "note-edit": "edit", "note-snooze": "snooze",
    "note-top": "top", "note-check": "check", "note-settings": "settings",
}
# Free-form wording ("move it to friday") is for Claude to turn into options, not an error.
CLAUDE_READS_FREE_FORM = {"edit", "snooze"}


def prompt_submit(stdin_text: str, now: datetime, home: Optional[Path] = None) -> Optional[Dict]:
    """Run note commands on this machine so Claude never receives them.

    Only prompts that start with a Notemind command are looked at; every other prompt
    returns None and carries on to Claude as usual. A handled command blocks the prompt
    and shows its result to the user. `note-add` is handled only when the built-in rules
    can read its date with confidence; otherwise Claude reads the note, as before.
    """
    try:
        prompt = json.loads(stdin_text or "{}").get("prompt", "")
    except (ValueError, AttributeError):
        return None
    if not isinstance(prompt, str):
        return None
    inline = INLINE_NOTE_RE.match(prompt)
    if inline:
        text = " ".join(inline.group(1).split())
        return _block(_add_inline(text, now, home or default_home())) if text else None
    match = COMMAND_RE.match(prompt)
    if not match:
        return None
    name, rest = match.group(1).lower(), (match.group(2) or "").strip()
    home = home or default_home()
    if name == "note-add":
        reason = _add_locally(" ".join(rest.split()), now, home)
    else:
        reason = _run_locally(LOCAL_COMMANDS[name], rest, now, home)
    return _block(reason)


def _block(reason: Optional[str]) -> Optional[Dict]:
    return {"decision": "block", "reason": reason} if reason else None


def _add_inline(text: str, now: datetime, home: Path) -> str:
    """`#note <text>`: always saved here, with no call to Claude. A date the built-in rules
    cannot read is not guessed; the note is saved without one and the user is told."""
    saved = _add_locally(text, now, home)
    if saved:
        return saved
    with NoteStore(home / "notes.db") as store:
        note = store.add(text)
    return (
        format_saved(note, [])
        + "\n\n*Saved without a date because it could not be read on its own. "
        "Set one with `/notemind:note-edit`.*"
    )


def _add_locally(text: str, now: datetime, home: Path) -> Optional[str]:
    """Save a note using only the built-in rules. Returns the message to show, or None to hand
    the prompt to Claude."""
    if not text:
        return None
    order = os.environ.get("NOTESCOS_DATE_ORDER", "dmy").lower()
    if order not in ("dmy", "mdy"):
        return None
    found = parse_due(text, now, order)
    if needs_claude(text, found):
        if find_sensitive(text):  # never hand a secret to Claude just to read a date
            return (
                "⚠️ **Not saved.** This note looks like it contains sensitive data, and Notemind "
                "could not read its date on its own, so it was not sent to Claude. "
                "Write the date in a simpler way (for example `tomorrow at 3pm` or `22 sep`) "
                "and try again, or add the note without a date."
            )
        return None
    with NoteStore(home / "notes.db") as store:
        note = store.add(text, due=found.due if found else None,
                         confirmed=ambiguity(text, found) is None)
    return format_saved(note, found.assumptions if found else [])


def _run_locally(command: str, rest: str, now: datetime, home: Path) -> Optional[str]:
    """Run `notescos <command> <args>` in-process and return its text, or None to defer to Claude."""
    from .cli import main  # imported here because cli imports this module

    try:
        argv = [command] + shlex.split(rest)
    except ValueError:  # unbalanced quote: let the command's own instructions handle it
        return None
    out, err = io.StringIO(), io.StringIO()
    previous = os.environ.get("NOTESCOS_HOME")
    os.environ["NOTESCOS_HOME"] = str(home)
    try:
        with redirect_stderr(err):
            code = main(argv, out=out, now=now)
    except SystemExit:  # arguments the tool does not understand
        free_form = len(argv) < 3 or not argv[2].startswith("-")
        if command in CLAUDE_READS_FREE_FORM and free_form:
            return None  # words like "move it to friday", not options: Claude reads them
        lines = err.getvalue().strip().splitlines()
        problem = lines[-1].split("error: ", 1)[-1] if lines else "unrecognised arguments"
        return f"⚠️ Could not read that: {problem}. Try `/notemind:note-help`."
    finally:
        if previous is None:
            os.environ.pop("NOTESCOS_HOME", None)
        else:
            os.environ["NOTESCOS_HOME"] = previous
    if code == 3:  # a date the built-in rules cannot read: Claude resolves it
        return None
    if code != 0:
        return "⚠️ " + (err.getvalue().strip().removeprefix("notescos: ") or "Something went wrong.")
    return out.getvalue().strip() or None


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


def log_error(home: Path, event: str = "hook") -> None:
    """Record a hook failure for later debugging without disturbing the session."""
    try:
        home.mkdir(parents=True, exist_ok=True)
        with open(home / "log", "a") as handle:
            handle.write(f"{datetime.now().isoformat(timespec='seconds')} {event}\n")
            handle.write(traceback.format_exc() + "\n")
    except OSError:
        pass
