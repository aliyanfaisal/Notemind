"""Command line entry point. Every command can print JSON for skills and hooks."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TextIO

from . import __version__
from .board import render_board
from .brief import (build_brief, format_done, format_edited, format_list, format_saved,
                    format_snoozed, format_today)
from . import settings as user_settings
from .hooks import log_error, prompt_submit, session_start
from .money import note_fields
from .parse import ambiguity, needs_claude, parse_due
from .redact import redact_note, redact_notes
from .report import (format_alert_set, format_check, format_forget, format_search, format_settings,
                     format_top)
from .score import rank
from .store import (ALERT_LEVELS, NOTE_TYPES, DateNotUnderstood, NoteError, NoteStore,
                    default_home)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notescos", description="Notemind: never forget a follow-up."
    )
    parser.add_argument("--version", action="version", version=f"notescos {__version__}")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument("--redact", action="store_true",
                        help="mask sensitive data (keys, passwords, card numbers...) in the output; "
                             "used when the output is going to Claude")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a note")
    add.add_argument("text", nargs="+",
                     help="the note text; use - to read it from stdin (safe for quotes and symbols)")
    add.add_argument("--type", choices=NOTE_TYPES,
                     help="default: task, or money_owed / money_due when the text says who owes whom")
    add.add_argument("--amount", type=float, help="money amount; read from the text when not given")
    add.add_argument("--currency", help="e.g. USD, PKR; read from the text when not given")
    add.add_argument("--due", help="exact due date: YYYY-MM-DD or YYYY-MM-DDTHH:MM, or 'none' for no date. "
                          "Without it, the date is read from the note text.")
    add.add_argument("--priority", type=int, choices=[0, 1, 2, 3], default=0)
    add.add_argument("--alert", choices=ALERT_LEVELS, default="normal", dest="alert_level")
    add.add_argument("--person")
    add.add_argument("--project")
    add.add_argument("--tag", action="append", dest="tags")

    ls = sub.add_parser("list", help="list notes")
    ls.add_argument("--all", action="store_true", help="include done notes")
    ls.add_argument("--type", choices=NOTE_TYPES)
    ls.add_argument("--project")
    _add_range_options(ls)

    board = sub.add_parser("board", help="write the notes board as an HTML page")
    _add_range_options(board)
    board.add_argument("--label", help="name of the range shown at the top, e.g. 'Next 2 days'")
    board.add_argument("--artifact", action="store_true",
                       help="write a page fragment for publishing as a Claude artifact")
    board.add_argument("--out", help="where to write the page (default: ~/.notescos/board.html)")

    sub.add_parser("today", help="what is overdue, due today and coming up")

    hook = sub.add_parser("hook", help="entry points used by Claude Code hooks")
    hook.add_argument("event", choices=["session-start", "prompt-submit"])

    done = sub.add_parser("done", help="mark a note done")
    done.add_argument("id", type=int)

    edit = sub.add_parser("edit", help="change a note")
    edit.add_argument("id", type=int)
    edit.add_argument("--text", help="new note text; use - to read it from stdin")
    edit.add_argument("--due", help="new due date in words or YYYY-MM-DD[THH:MM]; 'none' removes it")
    edit.add_argument("--type", choices=NOTE_TYPES)
    edit.add_argument("--amount", type=float, help="money amount; 0 or negative values are rejected")
    edit.add_argument("--currency", help="e.g. USD, PKR; 'none' removes it")
    edit.add_argument("--priority", type=int, choices=[0, 1, 2, 3])
    edit.add_argument("--confirm", action="store_true",
                      help="accept the note as it is, so it can alert")
    edit.add_argument("--alert", choices=ALERT_LEVELS, dest="alert_level")
    edit.add_argument("--person", help="'none' removes it")
    edit.add_argument("--project", help="'none' removes it")
    edit.add_argument("--tag", action="append", dest="tags",
                      help="replace the tags with these (repeat for several); --tag none clears them")

    top = sub.add_parser("top", help="the notes that matter most right now")
    top.add_argument("count", nargs="?", type=int, default=5)

    search = sub.add_parser("search", help="find notes that match a question")
    search.add_argument("question", nargs="+", help="the words to look for; use - to read them from stdin")
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--open", action="store_true", help="leave out finished notes")

    forget = sub.add_parser("forget", help="permanently delete notes")
    forget.add_argument("id", nargs="?", type=int, help="the note to delete")
    forget.add_argument("--project", help="delete every note in this project")
    forget.add_argument("--all", action="store_true", dest="everything", help="delete every note")
    forget.add_argument("--yes", action="store_true",
                        help="really delete (required for --project and --all)")

    sub.add_parser("check", help="overdue, due soon and follow-ups waiting too long")

    settings = sub.add_parser("settings", help="show or change settings")
    settings.add_argument("key", nargs="?", choices=["alert"])
    settings.add_argument("value", nargs="?")

    snooze = sub.add_parser("snooze", help="hide a note until later")
    snooze.add_argument("id", type=int)
    snooze.add_argument("when", nargs="*", help="when it should come back: 'tomorrow', '3 days', 'friday 9am'")
    snooze.add_argument("--clear", action="store_true", help="bring the note back now")
    return parser


def _add_range_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--from", dest="due_from", metavar="YYYY-MM-DD",
                        help="only notes due on or after this day")
    parser.add_argument("--to", dest="due_to", metavar="YYYY-MM-DD",
                        help="only notes due on or before this day")
    parser.add_argument("--overdue", action="store_true", help="only notes past their due time")


def _ranged_notes(store: NoteStore, args, now: datetime) -> List[dict]:
    notes = store.list(
        status=None if getattr(args, "all", False) else "active",
        type=getattr(args, "type", None), project=getattr(args, "project", None),
        due_from=args.due_from, due_to=args.due_to,
    )
    if args.overdue:
        overdue = {n["id"] for n in build_brief(notes, now).overdue}
        notes = [n for n in notes if n["id"] in overdue]
    return notes


_SHORT_SPAN = re.compile(r"^(\d+)\s*(m|min|mins|minutes?|h|hr|hrs|hours?|d|days?|w|weeks?)$", re.IGNORECASE)


def read_date(phrase: str, now: datetime, order: str) -> str:
    """Turn words like 'friday 5pm' into YYYY-MM-DD[THH:MM] using only the built-in rules.

    Raises DateNotUnderstood when the rules cannot be sure, so a caller can hand the
    wording to Claude instead of saving a guess.
    """
    phrase = " ".join(phrase.split())
    short = _SHORT_SPAN.match(phrase)
    if short:  # "3 days" or "2h" mean "in 3 days" / "in 2h"
        unit = {"m": "minutes", "h": "hours", "d": "days", "w": "weeks"}[short[2][0].lower()]
        phrase = f"in {short[1]} {unit}"
    found = parse_due(phrase, now, order)
    if not found or needs_claude(phrase, found):
        raise DateNotUnderstood(f"Could not read the date {phrase!r}.")
    return found.due


def _date_order() -> str:
    order = os.environ.get("NOTESCOS_DATE_ORDER", "dmy").lower()
    if order not in ("dmy", "mdy"):
        raise NoteError("NOTESCOS_DATE_ORDER must be 'dmy' or 'mdy'.")
    return order


SANDBOX_WARNING = (
    "⚠ This ran in a cloud sandbox, so your notes were NOT saved on your computer. "
    "Use Notemind from Claude Code on your machine (terminal, VS Code or the app's Code tab)."
)


def in_sandbox() -> bool:
    """True when running from the app's cloud skill sandbox (/mnt/skills/...)."""
    return os.path.abspath(__file__).startswith("/mnt/skills/")


def main(argv: Optional[List[str]] = None, out: Optional[TextIO] = None,
         now: Optional[datetime] = None) -> int:
    out = out or sys.stdout
    now = now or datetime.now()
    args = build_parser().parse_args(argv)
    if args.command == "hook":
        return _run_hook(args.event, out, now)
    try:
        with NoteStore() as store:
            store.wake(now)  # bring back snoozed notes whose time has come
            if args.command == "add":
                text = " ".join(args.text)
                if args.text == ["-"]:
                    text = " ".join(sys.stdin.read().split())
                # An explicit --due wins; otherwise read the date from the sentence.
                order = _date_order()
                if args.due and args.due.lower() == "none":
                    found, due = None, None  # the caller decided this note has no date
                else:
                    found = parse_due(args.due or text, now, order)
                    due = found.due if found else args.due
                # A date that came from the user's words, not an explicit --due, may be a guess.
                unclear = None if args.due else ambiguity(text, found, args.type)
                money = note_fields(text)  # who owes whom, read from the words
                if args.type:
                    money.pop("type", None)
                fields = {"type": args.type or "task", **money}
                for key, value in (("amount", args.amount), ("currency", args.currency),
                                   ("person", args.person)):
                    if value is not None:
                        fields[key] = value
                note = store.add(
                    text, due=due, priority=args.priority, alert_level=args.alert_level,
                    project=args.project, tags=args.tags, confirmed=unclear is None, **fields,
                )
                assumptions = found.assumptions if found else []
                if args.redact:
                    note, _ = redact_note(note)
                if args.json:
                    print(json.dumps({**note, "assumptions": assumptions}), file=out)
                else:
                    print(format_saved(note, assumptions), file=out)
            elif args.command == "list":
                notes = _ranged_notes(store, args, now)
                if args.redact:
                    notes, _ = redact_notes(notes)
                if args.json:
                    print(json.dumps(notes), file=out)
                else:
                    print(format_list(notes, now), file=out)
            elif args.command == "board":
                notes = _ranged_notes(store, args, now)
                masked = 0
                if args.artifact or args.redact:  # an artifact is published to claude.ai
                    notes, masked = redact_notes(notes)
                path = Path(args.out).expanduser() if args.out else default_home() / "board.html"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    render_board(notes, now, args.label, standalone=not args.artifact, masked=masked),
                    encoding="utf-8",
                )
                if args.json:
                    print(json.dumps({"path": str(path), "count": len(notes)}), file=out)
                else:
                    hidden = f" · {masked} sensitive item{'s' if masked != 1 else ''} masked" if masked else ""
                    print(f"🗂️ **Board ready** · {len(notes)} note{'s' if len(notes) != 1 else ''}{hidden}\n\n"
                          f"`{path}`", file=out)
            elif args.command == "today":
                notes = store.list()
                if args.redact:
                    notes, _ = redact_notes(notes)
                brief = build_brief(notes, now)
                print(json.dumps(brief.as_dict()) if args.json else format_today(brief, now),
                      file=out)
            elif args.command == "edit":
                changes = {}
                if args.text is not None:
                    changes["text"] = " ".join(sys.stdin.read().split()) if args.text == "-" else args.text
                if args.due is not None:
                    changes["due"] = None if args.due.lower() == "none" else read_date(
                        args.due, now, _date_order())
                if args.type is not None:
                    changes["type"] = args.type
                if args.priority is not None:
                    changes["priority"] = args.priority
                if args.amount is not None:
                    changes["amount"] = args.amount
                if args.currency is not None:
                    changes["currency"] = None if args.currency.lower() == "none" else args.currency
                if args.alert_level is not None:
                    changes["alert_level"] = args.alert_level
                for name in ("person", "project"):
                    value = getattr(args, name)
                    if value is not None:
                        changes[name] = None if value.lower() == "none" else value
                if args.tags is not None:
                    changes["tags"] = [] if [t.lower() for t in args.tags] == ["none"] else args.tags
                if args.confirm:
                    changes["confirmed"] = True
                if not changes:
                    raise NoteError("Nothing to change. Use --text, --due, --priority, --alert, "
                                    "--type, --amount, --currency, --person, --project, --tag or --confirm.")
                old = store.get(args.id)
                new = store.update(args.id, **changes)
                if args.redact:
                    old, new = redact_note(old)[0], redact_note(new)[0]
                print(json.dumps(new) if args.json else format_edited(old, new), file=out)
            elif args.command == "snooze":
                until = None
                if not args.clear:
                    if not args.when:
                        raise NoteError("Say when it should come back, for example: snooze 3 tomorrow.")
                    until = read_date(" ".join(args.when), now, _date_order())
                    if datetime.fromisoformat(until) <= now.replace(second=0, microsecond=0):
                        raise NoteError("That time has already passed. Pick a later time.")
                note = store.snooze(args.id, until)
                if args.redact:
                    note, _ = redact_note(note)
                print(json.dumps(note) if args.json else format_snoozed(note), file=out)
            elif args.command == "search":
                question = " ".join(args.question)
                if args.question == ["-"]:
                    question = " ".join(sys.stdin.read().split())
                found = store.search(question, limit=max(1, args.limit), include_done=not args.open)
                if args.redact:
                    found, _ = redact_notes(found)
                print(json.dumps(found) if args.json else format_search(question, found, now),
                      file=out)
            elif args.command == "forget":
                chosen = [args.id is not None, args.project is not None, args.everything]
                if sum(chosen) != 1:
                    raise NoteError("Pick one: a note number, --project NAME or --all.")
                what = (f"note #{args.id}" if args.id is not None
                        else f"project {args.project}" if args.project is not None else "all notes")
                # One note goes at once; a whole project or everything needs --yes.
                confirmed = args.id is not None or args.yes
                found = store.forget(note_id=args.id, project=args.project,
                                     everything=args.everything, dry_run=not confirmed)
                if args.redact:
                    found, _ = redact_notes(found)
                print(json.dumps({"deleted": confirmed, "notes": found}) if args.json
                      else format_forget(found, what, confirmed), file=out)
            elif args.command in ("top", "check"):
                notes = store.list()
                if args.redact:
                    notes, _ = redact_notes(notes)
                if args.command == "top":
                    if args.count < 1:
                        raise NoteError("Say how many notes to show, for example: top 5.")
                    ranked = rank(notes, now, user_settings.load(default_home()).get("weights"))
                    print(json.dumps(ranked[: args.count]) if args.json
                          else format_top(ranked, args.count), file=out)
                else:
                    print(format_check(notes, now), file=out)
            elif args.command == "settings":
                home = default_home()
                if args.key == "alert":
                    if not args.value:
                        raise NoteError("Say which level: quiet, normal or loud.")
                    level = user_settings.set_alert_level(home, args.value)["alert_level"]
                    print(format_alert_set(level), file=out)
                else:
                    print(format_settings(user_settings.load(home)), file=out)
            elif args.command == "done":
                note = store.done(args.id)
                if args.redact:
                    note, _ = redact_note(note)
                print(json.dumps(note) if args.json else format_done(note), file=out)
    except DateNotUnderstood as err:
        print(f"notescos: {err}", file=sys.stderr)
        return 3  # the caller may ask Claude to read the date instead
    except NoteError as err:
        print(f"notescos: {err}", file=sys.stderr)
        return 1
    if not getattr(args, "json", False) and in_sandbox():
        print(SANDBOX_WARNING, file=out)
    return 0


def _run_hook(event: str, out: TextIO, now: datetime) -> int:
    """Hooks never fail loudly: on any error, log it and let the session carry on."""
    try:
        stdin_text = "" if sys.stdin.isatty() else sys.stdin.read()
        handler = prompt_submit if event == "prompt-submit" else session_start
        result = handler(stdin_text, now)
        if result:
            print(json.dumps(result), file=out)
    except Exception:  # noqa: BLE001 - a hook must not break the user's session
        log_error(default_home(), event)
    return 0


def run() -> None:
    sys.exit(main())
