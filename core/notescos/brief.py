"""Turn a list of notes into the briefing shown at session start and by /cos:notes-today."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Tuple


def split_due(due_at: str) -> Tuple[date, Optional[time]]:
    """'2026-10-09' -> (date, None); '2026-10-09T15:00' -> (date, time)."""
    if len(due_at) == 10:
        return date.fromisoformat(due_at), None
    stamp = datetime.fromisoformat(due_at)
    return stamp.date(), stamp.time()


def _sort_key(note: Dict):
    day, at = split_due(note["due_at"])
    return day, at or time.max, note["id"]


@dataclass
class Brief:
    overdue: List[Dict]
    due_today: List[Dict]
    upcoming: List[Dict]
    undated: List[Dict]

    def as_dict(self) -> Dict[str, List[Dict]]:
        return {
            "overdue": self.overdue, "due_today": self.due_today,
            "upcoming": self.upcoming, "undated": self.undated,
        }

    @property
    def attention(self) -> int:
        return len(self.overdue) + len(self.due_today) + len(self.upcoming)


def build_brief(
    notes: List[Dict], now: datetime, horizon_days: int = 7, skip_silent: bool = False
) -> Brief:
    """Sort open notes into overdue / today / upcoming (within the horizon) / undated."""
    today = now.date()
    last_day = today + timedelta(days=horizon_days)
    overdue, due_today, upcoming, undated = [], [], [], []
    for note in notes:
        if note["status"] != "open":
            continue
        if skip_silent and note["alert_level"] == "silent":
            continue
        if not note["due_at"]:
            undated.append(note)
            continue
        day, at = split_due(note["due_at"])
        if day < today or (day == today and at is not None and at <= now.time()):
            overdue.append(note)
        elif day == today:
            due_today.append(note)
        elif day <= last_day:
            upcoming.append(note)
    for group in (overdue, due_today, upcoming):
        group.sort(key=_sort_key)
    return Brief(overdue, due_today, upcoming, undated)


def when_label(note: Dict, now: datetime) -> str:
    """Short human wording for a due date: 'overdue 2d', 'today 15:00', 'Fri 9 Oct'."""
    today = now.date()
    day, at = split_due(note["due_at"])
    clock = f" {at:%H:%M}" if at else ""
    if day < today:
        return f"overdue {(today - day).days}d"
    if day == today:
        return f"today{clock}" if not at or at > now.time() else "overdue today"
    if day == today + timedelta(days=1):
        return f"tomorrow{clock}"
    return f"{day:%a} {day.day} {day:%b}{clock}"


def _item(note: Dict, now: datetime) -> str:
    return f"#{note['id']} {note['text']} ({when_label(note, now)})"


def format_banner(brief: Brief, now: datetime, max_items: int = 4) -> str:
    """The short block shown when a session starts. Empty when nothing needs attention."""
    if not brief.attention:
        return ""
    counts = [
        f"{len(group)} {label}"
        for group, label in (
            (brief.overdue, "overdue"), (brief.due_today, "due today"),
            (brief.upcoming, "coming up"),
        )
        if group
    ]
    lines = ["📌 Notes: " + " · ".join(counts)]
    entries = [("!", n) for n in brief.overdue] + [
        ("•", n) for n in brief.due_today + brief.upcoming
    ]
    for mark, note in entries[:max_items]:
        lines.append(f"  {mark} {_item(note, now)}")
    if len(entries) > max_items:
        lines.append(f"  …and {len(entries) - max_items} more")
    lines.append("  /cos:notes-today for details")
    return "\n".join(lines)


def format_today(brief: Brief, now: datetime, max_undated: int = 5) -> str:
    """The fuller view behind /cos:notes-today."""
    if not (brief.attention or brief.undated):
        return "No open notes yet. Add one with: /cos:notes-add <your note here>"
    sections = []
    for title, group in (
        ("Overdue", brief.overdue), ("Due today", brief.due_today),
        ("Coming up (next 7 days)", brief.upcoming),
    ):
        if group:
            body = "\n".join(f"  {_item(n, now)}" for n in group)
            sections.append(f"{title} ({len(group)})\n{body}")
    if brief.undated:
        shown = brief.undated[:max_undated]
        body = "\n".join(f"  #{n['id']} {n['text']}" for n in shown)
        extra = len(brief.undated) - len(shown)
        if extra > 0:
            body += f"\n  …and {extra} more (see /cos:notes-list)"
        sections.append(f"No date ({len(brief.undated)})\n{body}")
    if not brief.attention:
        sections.insert(0, "Nothing is due in the next 7 days.")
    return "\n\n".join(sections)
