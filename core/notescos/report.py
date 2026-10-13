"""Markdown views for note-top, note-check and note-settings."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from .brief import _cell, _table, build_brief, due_label, needs_input_lines, when_label
from .score import is_alertable, rank, stale_days
from .settings import ALERT_LEVELS

LEVEL_HELP = {
    "quiet": "only overdue notes and notes marked urgent",
    "normal": "overdue, due today, due in the next 2 days, and follow-ups waiting 3+ days",
    "loud": "the same as normal, looking 7 days ahead",
}


def format_top(ranked: List[Dict], count: int) -> str:
    """The `count` highest-priority notes with the reason each one ranks there."""
    if not ranked:
        return "✅ **Nothing to prioritise.** You have no open notes."
    shown = ranked[:count]
    rows = ["| Note | Why |", "|---|---|"]
    rows += [f"| **#{n['id']}** {_cell(n['text'])} | {n['why']} |" for n in shown]
    more = len(ranked) - len(shown)
    tail = [""] + [f"*{more} more open. `note-top {len(ranked)}` shows all.*"] if more > 0 else []
    return "\n".join([f"### 🔝 Top {len(shown)}", ""] + rows + tail)


def format_check(notes: List[Dict], now: datetime) -> str:
    """Overdue, due today, due soon, and follow-ups waiting too long."""
    live = [n for n in notes if is_alertable(n)]
    unclear = [n for n in notes if n["status"] == "open" and not n["confirmed"]]
    brief = build_brief(live, now, horizon_days=2)
    shown = {n["id"] for n in brief.overdue + brief.due_today + brief.upcoming}
    waiting = sorted(
        ((stale_days(n, now), n) for n in live if n["id"] not in shown and stale_days(n, now)),
        key=lambda pair: (-pair[0], pair[1]["id"]),
    )
    lines = [f"### 🔎 Check · {now:%a} {now.day} {now:%b}", ""]
    if not (brief.overdue or brief.due_today or brief.upcoming or waiting):
        clear = "✅ **All clear.** Nothing is overdue, due soon or waiting on a reply."
        return "\n".join(lines + [clear] + needs_input_lines(unclear))
    for group, title, last in (
        (brief.overdue, "🔴 Overdue", "Was due"), (brief.due_today, "🟠 Due today", "When"),
        (brief.upcoming, "🔵 Due in the next 2 days", "When"),
    ):
        if group:
            lines += [f"**{title} ({len(group)})**", ""] + _table(group, now, last) + [""]
    if waiting:
        lines += [f"**⏳ Waiting on a reply ({len(waiting)})**", "", "| Note | Waiting |", "|---|---|"]
        lines += [f"| **#{n['id']}** {_cell(n['text'])} | {days} days |" for days, n in waiting] + [""]
    lines += needs_input_lines(unclear)
    return "\n".join(lines).rstrip()


def format_search(question: str, found: List[Dict], now: datetime) -> str:
    """Markdown table of the notes that matched a question, with their ids to cite."""
    if not found:
        return f"*No notes match “{question}”.*"
    rows = ["| Note | Status | Due |", "|---|---|---|"]
    for n in found:
        status = "✅ done" if n["status"] == "done" else (
            "💤 snoozed" if n["status"] == "snoozed" else "open")
        due = when_label(n, now) if n["due_at"] and n["status"] == "open" else (
            due_label(n) if n["due_at"] else "")
        rows.append(f"| **#{n['id']}** {_cell(n['text'])} | {status} | {due} |")
    return "\n".join([f"### 🔍 {len(found)} match{'es' if len(found) != 1 else ''}", ""] + rows)


def format_settings(config: Dict) -> str:
    current = config["alert_level"]
    rows = ["| Alert level | Startup banner shows |", "|---|---|"]
    for level in ALERT_LEVELS:
        mark = "**✓ " + level + "**" if level == current else level
        rows.append(f"| {mark} | {LEVEL_HELP[level]} |")
    return "\n".join(
        ["### ⚙️ Settings", ""] + rows + ["",
         "*Change it with `note-settings alert quiet`, `normal` or `loud`. A single note can be "
         "kept out of alerts with `note-edit <number> --alert silent`, or always shown with `--alert urgent`.*"])


def format_alert_set(level: str) -> str:
    return f"⚙️ **Alert level set to {level}** · the startup banner now shows {LEVEL_HELP[level]}."
