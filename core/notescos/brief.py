"""Turn a list of notes into the briefing shown at session start and by /notemind:note-today."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Tuple

from .money import format_amount, totals


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
    unconfirmed: List[Dict] = field(default_factory=list)  # waiting for the user's answer
    money: List[Dict] = field(default_factory=list)  # open money notes, whenever they fall due

    def as_dict(self) -> Dict[str, List[Dict]]:
        return {
            "overdue": self.overdue, "due_today": self.due_today,
            "upcoming": self.upcoming, "undated": self.undated,
            "needs_input": self.unconfirmed, "money": self.money,
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
    overdue, due_today, upcoming, undated, unconfirmed, money = [], [], [], [], [], []
    for note in notes:
        if note["status"] != "open":
            continue
        if not note["confirmed"]:
            unconfirmed.append(note)
            continue
        if skip_silent and note["alert_level"] == "silent":
            continue
        if note["type"] in MONEY_TYPES:
            money.append(note)
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
    return Brief(overdue, due_today, upcoming, undated, unconfirmed, money)


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


def _cell(text: str, limit: int = 60) -> str:
    text = " ".join(text.split()).replace("|", "/")
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def stamp_label(value: str) -> str:
    """Absolute date for display: 'Fri 9 Oct, 16:00' or 'Fri 9 Oct'."""
    day, at = split_due(value)
    label = f"{day:%a} {day.day} {day:%b}"
    return f"{label}, {at:%H:%M}" if at else label


def due_label(note: Dict) -> str:
    return stamp_label(note["due_at"]) if note["due_at"] else "No date"


def _table(notes: List[Dict], now: datetime, last: str) -> List[str]:
    rows = [f"| Note | {last} |", "|---|---|"]
    rows += [f"| **#{n['id']}** {_cell(n['text'])} | {when_label(n, now)} |" for n in notes]
    return rows


def needs_input_lines(unconfirmed: List[Dict]) -> List[str]:
    """Markdown lines asking the user about notes whose date is still unclear."""
    if not unconfirmed:
        return []
    ids = ", ".join(f"#{n['id']}" for n in unconfirmed)
    plural = "s" if len(unconfirmed) != 1 else ""
    return ["", f"> ❓ **{len(unconfirmed)} note{plural} need{'' if plural else 's'} your input** ({ids}). "
                f"Their date is unclear, so they will not alert until you confirm. "
                f"Use `note-edit <number> --confirm`, or give a date."]


def money_lines(money: List[Dict], now: datetime) -> List[str]:
    """Who owes you and what you owe, with totals per currency. Empty when there is none."""
    if not money:
        return []
    ordered = sorted(money, key=lambda n: (n["type"] != "money_owed", n["due_at"] is None,
                                           n["due_at"] or "", n["id"]))
    rows = ["| | Note | Amount | When |", "|:-:|---|--:|---|"]
    for n in ordered:
        icon = "💰" if n["type"] == "money_owed" else "💸"
        when = when_label(n, now) if n["due_at"] else ""
        rows.append(f"| {icon} | **#{n['id']}** {_cell(n['text'], 50)} | "
                    f"{format_amount(n.get('amount'), n.get('currency')) or '?'} | {when} |")
    summary = []
    for kind, label in (("money_owed", "Owed to you"), ("money_due", "You owe")):
        parts = [format_amount(v, c) for c, v in totals(money, kind).items()]
        if parts:
            summary.append(f"**{label}:** {' + '.join(parts)}")
    tail = ["", " · ".join(summary)] if summary else []
    return ["**💵 Money**", ""] + rows + tail + [""]


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
    if brief.money and lines[-1]:
        lines.append("")
    lines += money_lines(brief.money, now)
    more = []
    if brief.upcoming:
        more.append(f"{len(brief.upcoming)} coming up")
    if brief.undated:
        more.append(f"{len(brief.undated)} without a date")
    if more:
        lines.append(f"*{' · '.join(more)}. See `note-list`.*")
    lines += needs_input_lines(brief.unconfirmed)
    return "\n".join(lines).rstrip()


def format_list(notes: List[Dict], now: datetime, show_done: bool = False) -> str:
    """Markdown table of notes."""
    if not notes:
        return "*No notes yet. Add one with `note-add`.*"
    open_count = sum(1 for n in notes if n["status"] == "open")
    snoozed = sum(1 for n in notes if n["status"] == "snoozed")
    head = f"### 🗒️ Notes · {open_count} open" + (f" · {snoozed} snoozed" if snoozed else "")
    rows = ["| Note | Due | Status |", "|---|---|---|"]
    for n in notes:
        if n["status"] == "done":
            due, status = due_label(n), "✅ Done"
        elif n["status"] == "snoozed":
            due, status = due_label(n) if n["due_at"] else "—", f"💤 until {stamp_label(n['snoozed_until'])}"
        elif not n["due_at"]:
            due, status = "—", "Open"
        else:
            label = when_label(n, now)
            icon = "🔴" if label.startswith("overdue") else "🟠" if label.startswith("today") else "🔵"
            due, status = due_label(n), f"{icon} {label}"
        rows.append(f"| **#{n['id']}** {_cell(n['text'])} | {due} | {status} |")
    return "\n".join([head, ""] + rows)


MONEY_TYPES = ("money_owed", "money_due")


def money_line(note: Dict) -> str:
    """One line about the money in a note, e.g. '💰 **Ali owes you** 15,000 PKR'."""
    amount = format_amount(note.get("amount"), note.get("currency")) or "an amount not given"
    who = note.get("person")
    if note["type"] == "money_owed":
        return f"💰 **{who + ' owes' if who else 'Owed to'} you** {amount}"
    return f"💸 **You owe{' ' + who if who else ''}** {amount}"


def format_saved(note: Dict, assumptions: List[str]) -> str:
    """Markdown confirmation after note-add."""
    lines = [f"✅ **Saved** · #{note['id']} {note['text']}", ""]
    lines.append(f"📅 **Due:** {due_label(note)}" if note["due_at"] else "🗒️ **No due date**")
    if note["type"] in MONEY_TYPES:
        lines += ["", money_line(note)]
    for item in assumptions:
        lines += ["", f"> ⚠️ {item}"]
    if not note["confirmed"]:
        lines += ["", f"> ❓ **Needs your input.** This will not alert until you confirm it: "
                      f"`note-edit {note['id']} --confirm`, or give it a date with `--due`."]
    return "\n".join(lines)


def format_done(note: Dict) -> str:
    return f"✅ **Done** · #{note['id']} {note['text']}"


def format_snoozed(note: Dict) -> str:
    if note["status"] == "snoozed":
        return (f"💤 **Snoozed** · #{note['id']} {note['text']}\n\n"
                f"⏰ **Back on:** {stamp_label(note['snoozed_until'])}")
    return f"⏰ **Back on your list** · #{note['id']} {note['text']}"


_EDIT_LABELS = (
    ("text", "Note"), ("type", "Type"), ("due_at", "Due"), ("priority", "Priority"),
    ("alert_level", "Alert"), ("amount", "Amount"), ("currency", "Currency"), ("confirmed", "Confirmed"), ("person", "Person"), ("project", "Project"), ("tags", "Tags"),
)


def _edit_value(field: str, value) -> str:
    if value in (None, "", []):
        return "none" if field != "priority" else "none"
    if field == "due_at":
        return stamp_label(value)
    if field == "tags":
        return ", ".join(value)
    if field == "confirmed":
        return "yes" if value else "no, needs your input"
    return str(value).replace("_", " ") if field == "type" else str(value)


def format_edited(old: Dict, new: Dict) -> str:
    """Markdown summary of what note-edit changed."""
    changes = [(label, old[f], new[f], f) for f, label in _EDIT_LABELS if old[f] != new[f]]
    if not changes:
        return f"ℹ️ **Nothing changed** · #{new['id']} {new['text']}"
    lines = [f"✏️ **Updated** · #{new['id']} {new['text']}", ""]
    lines += [f"- **{label}:** {_edit_value(f, a)} → {_edit_value(f, b)}" for label, a, b, f in changes]
    return "\n".join(lines)
