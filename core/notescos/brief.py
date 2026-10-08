"""Turn a list of notes into the briefing shown at session start and by /notemind:note-today."""

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
        """Notes that need action now: overdue and due today."""
        return len(self.overdue) + len(self.due_today)


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
        )
        if group
    ]
    lines = ["📌 Notes: " + " · ".join(counts)]
    entries = [("!", n) for n in brief.overdue] + [("•", n) for n in brief.due_today]
    for mark, note in entries[:max_items]:
        lines.append(f"  {mark} {_item(note, now)}")
    if len(entries) > max_items:
        lines.append(f"  …and {len(entries) - max_items} more")
    lines.append("  /notemind:note-today for details")
    return "\n".join(lines)


def format_banner_markdown(brief: Brief, now: datetime, max_items: int = 3) -> str:
    """A compact markdown card for clients that show Claude's reply, not hook messages."""
    if not brief.attention:
        return ""
    counts = [
        f"{len(group)} {label}"
        for group, label in (
            (brief.overdue, "overdue"), (brief.due_today, "due today"),
        )
        if group
    ]
    rows = [("🔴", n) for n in brief.overdue] + [("🟠", n) for n in brief.due_today]
    lines = [f"> **📌 Notemind** · {' · '.join(counts)}", ">"]
    lines.append("> | | Note | When |")
    lines.append("> |:-:|---|---|")
    for icon, note in rows[:max_items]:
        text = " ".join(note["text"].split()).replace("|", "/")
        text = text if len(text) <= 48 else text[:47].rstrip() + "…"
        lines.append(f"> | {icon} | #{note['id']} {text} | {when_label(note, now)} |")
    hidden = len(rows) - max_items
    tail = f"+{hidden} more · " if hidden > 0 else ""
    lines += [">", f"> *{tail}/note-today for the full list*"]
    return "\n".join(lines)


def _cell(text: str, limit: int = 60) -> str:
    text = " ".join(text.split()).replace("|", "/")
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def due_label(note: Dict) -> str:
    """Absolute due date for display: 'Fri 9 Oct, 16:00' or 'Fri 9 Oct'."""
    if not note["due_at"]:
        return "No date"
    day, at = split_due(note["due_at"])
    label = f"{day:%a} {day.day} {day:%b}"
    return f"{label}, {at:%H:%M}" if at else label


def _table(notes: List[Dict], now: datetime, last: str) -> List[str]:
    rows = [f"| # | Note | {last} |", "|--:|---|---|"]
    rows += [f"| {n['id']} | {_cell(n['text'])} | {when_label(n, now)} |" for n in notes]
    return rows


def format_today(brief: Brief, now: datetime) -> str:
    """Markdown view behind note-today: only what is overdue or due today."""
    lines = [f"### 📌 Today · {now:%a} {now.day} {now:%b}", ""]
    if not brief.attention:
        lines.append("✅ **All clear.** Nothing is overdue or due today.")
    if brief.overdue:
        lines += [f"**🔴 Overdue ({len(brief.overdue)})**", ""]
        lines += _table(brief.overdue, now, "Was due") + [""]
    if brief.due_today:
        lines += [f"**🟠 Due today ({len(brief.due_today)})**", ""]
        lines += _table(brief.due_today, now, "When") + [""]
    more = []
    if brief.upcoming:
        more.append(f"{len(brief.upcoming)} coming up")
    if brief.undated:
        more.append(f"{len(brief.undated)} without a date")
    if more:
        lines.append(f"*{' · '.join(more)}. See `note-list`.*")
    return "\n".join(lines).rstrip()


def format_list(notes: List[Dict], now: datetime, show_done: bool = False) -> str:
    """Markdown table of notes."""
    if not notes:
        return "*No notes yet. Add one with `note-add`.*"
    open_count = sum(1 for n in notes if n["status"] == "open")
    head = f"### 🗒️ Notes · {open_count} open"
    rows = ["| # | Note | Due | Status |", "|--:|---|---|---|"]
    for n in notes:
        if n["status"] == "done":
            due, status = due_label(n), "✅ Done"
        elif not n["due_at"]:
            due, status = "—", "Open"
        else:
            label = when_label(n, now)
            icon = "🔴" if label.startswith("overdue") else "🟠" if label.startswith("today") else "🔵"
            due, status = due_label(n), f"{icon} {label}"
        rows.append(f"| {n['id']} | {_cell(n['text'])} | {due} | {status} |")
    return "\n".join([head, ""] + rows)


def format_saved(note: Dict, assumptions: List[str]) -> str:
    """Markdown confirmation after note-add."""
    lines = [f"✅ **Saved** · #{note['id']} {note['text']}", ""]
    lines.append(f"📅 **Due:** {due_label(note)}" if note["due_at"] else "🗒️ **No due date**")
    for item in assumptions:
        lines += ["", f"> ⚠️ {item}"]
    return "\n".join(lines)


def format_done(note: Dict) -> str:
    return f"✅ **Done** · #{note['id']} {note['text']}"
