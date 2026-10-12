"""The short block shown when a session starts, shaped by the alert level.

quiet   overdue notes and notes marked urgent
normal  overdue, due today, due in the next 2 days, and follow-ups waiting 3+ days
loud    the same, but looking 7 days ahead
Silent and snoozed notes never appear. The block is capped so it never takes over the screen.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple

from .brief import build_brief, when_label
from .score import is_alertable, stale_days

HORIZON = {"quiet": 2, "normal": 2, "loud": 7}
FOOTER = "/notemind:note-check for details"


def _select(notes: List[Dict], now: datetime, level: str):
    """Return (overdue, today, soon, waiting) lists for the level."""
    brief = build_brief(notes, now, HORIZON.get(level, 2), skip_silent=True)
    overdue, today, soon = brief.overdue, brief.due_today, brief.upcoming
    if level == "quiet":
        today = [n for n in today if n["alert_level"] == "urgent"]
        soon = [n for n in soon if n["alert_level"] == "urgent"]
        return overdue, today, soon, []
    shown = {n["id"] for n in overdue + today + soon}
    waiting = [n for n in notes if is_alertable(n) and n["id"] not in shown and stale_days(n, now)]
    return overdue, today, soon, waiting


def _counts(overdue, today, soon, waiting) -> str:
    parts = [
        f"{len(group)} {label}"
        for group, label in ((overdue, "overdue"), (today, "due today"), (soon, "due soon"),
                             (waiting, "waiting on a reply"))
        if group
    ]
    return " · ".join(parts)


def _text(note: Dict, limit: int) -> str:
    text = " ".join(note["text"].split()).replace("|", "/")
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def build_banner(notes: List[Dict], now: datetime, level: str = "normal",
                 markdown: bool = False, max_items: int = 4) -> str:
    """The banner text, or an empty string when nothing needs attention."""
    overdue, today, soon, waiting = _select(notes, now, level)
    rows: List[Tuple[str, Dict]] = (
        [("!", n) for n in overdue] + [("•", n) for n in today] + [("→", n) for n in soon]
    )
    if not rows and not waiting:
        return ""
    counts = _counts(overdue, today, soon, waiting)
    hidden = len(rows) - max_items
    if markdown:
        icons = {"!": "🔴", "•": "🟠", "→": "🔵"}
        lines = [f"> **📌 Notemind** · {counts}", ">", "> | | Note | When |", "> |:-:|---|---|"]
        for mark, note in rows[:3]:
            lines.append(f"> | {icons[mark]} | #{note['id']} {_text(note, 48)} | {when_label(note, now)} |")
        more = len(rows) - 3
        tail = f"+{more} more · " if more > 0 else ""
        return "\n".join(lines + [">", f"> *{tail}/note-check for the full list*"])
    lines = ["📌 Notes: " + counts]
    for mark, note in rows[:max_items]:
        lines.append(f"  {mark} #{note['id']} {_text(note, 60)} ({when_label(note, now)})")
    if hidden > 0:
        lines.append(f"  …and {hidden} more")
    lines.append("  " + FOOTER)
    return "\n".join(lines)
