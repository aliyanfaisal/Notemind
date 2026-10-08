"""Command line entry point. Every command can print JSON for skills and hooks."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Optional, TextIO

from . import __version__
from .parse import parse_due
from .store import ALERT_LEVELS, NOTE_TYPES, NoteError, NoteStore


def _line(note: dict) -> str:
    mark = "x" if note["status"] == "done" else " "
    bits = [f"[{mark}] #{note['id']}", note["text"]]
    if note["due_at"]:
        bits.append(f"(due {note['due_at']})")
    if note["project"]:
        bits.append(f"[{note['project']}]")
    return " ".join(bits)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notescos", description="Notes Chief of Staff: never forget a follow-up."
    )
    parser.add_argument("--version", action="version", version=f"notescos {__version__}")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a note")
    add.add_argument("text", nargs="+", help="the note text")
    add.add_argument("--type", choices=[t for t in NOTE_TYPES if not t.startswith("money_")],
                     default="task")
    add.add_argument("--due", help="optional override: a date like 2026-10-09 or 'next friday'")
    add.add_argument("--priority", type=int, choices=[0, 1, 2, 3], default=0)
    add.add_argument("--alert", choices=ALERT_LEVELS, default="normal", dest="alert_level")
    add.add_argument("--person")
    add.add_argument("--project")
    add.add_argument("--tag", action="append", dest="tags")

    ls = sub.add_parser("list", help="list notes")
    ls.add_argument("--all", action="store_true", help="include done notes")
    ls.add_argument("--type", choices=NOTE_TYPES)
    ls.add_argument("--project")

    done = sub.add_parser("done", help="mark a note done")
    done.add_argument("id", type=int)
    return parser


def main(argv: Optional[List[str]] = None, out: Optional[TextIO] = None,
         now: Optional[datetime] = None) -> int:
    out = out or sys.stdout
    now = now or datetime.now()
    args = build_parser().parse_args(argv)
    try:
        with NoteStore() as store:
            if args.command == "add":
                text = " ".join(args.text)
                # An explicit --due wins; otherwise read the date from the sentence.
                order = os.environ.get("NOTESCOS_DATE_ORDER", "dmy").lower()
                if order not in ("dmy", "mdy"):
                    raise NoteError("NOTESCOS_DATE_ORDER must be 'dmy' or 'mdy'.")
                found = parse_due(args.due or text, now, order)
                due = found.due if found else args.due
                note = store.add(
                    text, type=args.type, due=due,
                    priority=args.priority, alert_level=args.alert_level,
                    person=args.person, project=args.project, tags=args.tags,
                )
                assumptions = found.assumptions if found else []
                if args.json:
                    print(json.dumps({**note, "assumptions": assumptions}), file=out)
                else:
                    print(f"Added {_line(note)}", file=out)
                    for item in assumptions:
                        print(f"  ! {item}", file=out)
            elif args.command == "list":
                notes = store.list(
                    status=None if args.all else "open", type=args.type, project=args.project
                )
                if args.json:
                    print(json.dumps(notes), file=out)
                elif notes:
                    print("\n".join(_line(n) for n in notes), file=out)
                else:
                    print("No notes.", file=out)
            elif args.command == "done":
                note = store.done(args.id)
                print(json.dumps(note) if args.json else f"Done {_line(note)}", file=out)
    except NoteError as err:
        print(f"notescos: {err}", file=sys.stderr)
        return 1
    return 0


def run() -> None:
    sys.exit(main())
