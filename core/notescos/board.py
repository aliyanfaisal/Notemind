"""Render the notes board: one self-contained HTML page, no scripts and no network.

The same page is used two ways. Written as a local file it is a full HTML document.
Written for an artifact it is a fragment, because publishing wraps it in its own skeleton.
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import date, datetime, timedelta
from html import escape
from typing import Dict, List, Optional

from .brief import split_due, when_label

TITLE = "Notemind Board"

STYLE = """
/* Layout: a summary strip, then notes grouped by day, overdue first. */
:root {
  --bg: #f6f4f1; --surface: #ffffff; --ink: #231f1b; --muted: #6b645c; --line: #e3ded7;
  --accent: #d9622b;
  --overdue: #b42318; --overdue-bg: #fdecea;
  --today: #9a5b00; --today-bg: #fff3dc;
  --upcoming: #1d5fb8; --upcoming-bg: #e8f0fc;
  --done: #2f7a45; --done-bg: #e6f4ea;
  --nodate: #5c5650; --nodate-bg: #eeebe7;
  --sans: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #171412; --surface: #211d1a; --ink: #f1ece6; --muted: #a39b91; --line: #34302b;
    --accent: #f08a57;
    --overdue: #ff8a7d; --overdue-bg: #3a1c19;
    --today: #f2b04c; --today-bg: #3a2b12;
    --upcoming: #8db8f5; --upcoming-bg: #172536;
    --done: #7fd196; --done-bg: #17301f;
    --nodate: #bdb5ab; --nodate-bg: #2a2623;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #171412; --surface: #211d1a; --ink: #f1ece6; --muted: #a39b91; --line: #34302b;
  --accent: #f08a57;
  --overdue: #ff8a7d; --overdue-bg: #3a1c19;
  --today: #f2b04c; --today-bg: #3a2b12;
  --upcoming: #8db8f5; --upcoming-bg: #172536;
  --done: #7fd196; --done-bg: #17301f;
  --nodate: #bdb5ab; --nodate-bg: #2a2623;
  color-scheme: dark;
}
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--ink); font-family: var(--sans); line-height: 1.45; }
.board { max-width: 760px; margin: 0 auto; padding-inline: 16px; padding-block: 28px 56px; }
header h1 { font-size: 1.5rem; margin: 0; letter-spacing: -0.01em; text-wrap: balance; }
header h1 span { color: var(--accent); }
.range { margin: 4px 0 0; color: var(--muted); }
.stats { display: flex; flex-wrap: wrap; gap: 8px; margin: 18px 0 8px; padding: 0; list-style: none; }
.stats li { font-size: 0.85rem; padding: 4px 10px; border-radius: 999px; font-variant-numeric: tabular-nums; }
.stats strong { font-weight: 650; }
.day { margin-top: 26px; }
.day h2 {
  display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px;
  font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase; margin: 0 0 8px;
  color: var(--muted);
}
.day h2 .n { font-variant-numeric: tabular-nums; }
.day.overdue h2 { color: var(--overdue); }
.day.today h2 { color: var(--today); }
.notes { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.note {
  display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 4px 12px;
  background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px;
}
.id { font-family: var(--mono); font-size: 0.8rem; color: var(--muted); padding-top: 2px; }
.text { margin: 0; overflow-wrap: anywhere; }
.when { text-align: right; font-size: 0.85rem; color: var(--muted); font-variant-numeric: tabular-nums; white-space: nowrap; }
.meta { grid-column: 2 / -1; display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
.chip { font-size: 0.75rem; padding: 1px 8px; border-radius: 4px; background: var(--nodate-bg); color: var(--nodate); }
.pill { font-size: 0.75rem; font-weight: 600; padding: 1px 8px; border-radius: 999px; }
.s-overdue { background: var(--overdue-bg); color: var(--overdue); }
.s-today { background: var(--today-bg); color: var(--today); }
.s-upcoming { background: var(--upcoming-bg); color: var(--upcoming); }
.s-done { background: var(--done-bg); color: var(--done); }
.s-nodate { background: var(--nodate-bg); color: var(--nodate); }
.note.is-done .text { text-decoration: line-through; color: var(--muted); }
.empty {
  margin-top: 28px; padding: 28px 16px; text-align: center; color: var(--muted);
  border: 1px dashed var(--line); border-radius: 8px;
}
.empty strong { display: block; color: var(--ink); font-size: 1.05rem; margin-bottom: 4px; }
footer { margin-top: 36px; font-size: 0.78rem; color: var(--muted); }
@media (max-width: 440px) {
  .note { grid-template-columns: auto minmax(0, 1fr); }
  .when { grid-column: 2; text-align: left; }
}
"""


def _status(note: Dict, now: datetime):
    """(css class, short label) for a note's state."""
    if note["status"] == "done":
        return "s-done", "Done"
    if not note["due_at"]:
        return "s-nodate", "No date"
    label = when_label(note, now)
    if label.startswith("overdue"):
        return "s-overdue", label.capitalize()
    if label.startswith("today"):
        return "s-today", "Due today"
    return "s-upcoming", "Upcoming"


def _day_heading(day: date, today: date) -> str:
    base = f"{day:%a} {day.day} {day:%b}"
    if day == today:
        return f"Today · {base}"
    if day == today + timedelta(days=1):
        return f"Tomorrow · {base}"
    return base


def _group(notes: List[Dict], today: date) -> "OrderedDict[str, Dict]":
    """Overdue first, then one group per day, then notes without a date."""
    overdue, days, undated = [], {}, []
    for note in notes:
        if not note["due_at"]:
            undated.append(note)
            continue
        day, _ = split_due(note["due_at"])
        if day < today and note["status"] == "open":
            overdue.append(note)
        else:
            days.setdefault(day, []).append(note)
    groups: "OrderedDict[str, Dict]" = OrderedDict()
    if overdue:
        groups["overdue"] = {"title": "Overdue", "css": "overdue", "notes": overdue}
    for day in sorted(days):
        css = "today" if day == today else "upcoming"
        groups[day.isoformat()] = {"title": _day_heading(day, today), "css": css, "notes": days[day]}
    if undated:
        groups["none"] = {"title": "No date", "css": "nodate", "notes": undated}
    return groups


def _note_html(note: Dict, now: datetime) -> str:
    css, label = _status(note, now)
    when = "—"
    if note["due_at"]:
        day, at = split_due(note["due_at"])
        when = f"{day:%a} {day.day} {day:%b}" + (f", {at:%H:%M}" if at else "")
    chips = [note["type"].replace("_", " ")]
    if note.get("person"):
        chips.append(f"with {note['person']}")
    if note.get("project"):
        chips.append(f"project {note['project']}")
    if note.get("priority"):
        chips.append(f"priority {note['priority']}")
    chips += [f"#{t}" for t in note.get("tags") or []]
    chip_html = "".join(f'<span class="chip">{escape(c)}</span>' for c in chips)
    done = " is-done" if note["status"] == "done" else ""
    return (
        f'<li class="note{done}">'
        f'<span class="id">#{note["id"]}</span>'
        f'<p class="text">{escape(note["text"])}</p>'
        f'<span class="when">{escape(when)}</span>'
        f'<div class="meta"><span class="pill {css}">{escape(label)}</span>{chip_html}</div>'
        "</li>"
    )


def _stats(notes: List[Dict], now: datetime) -> str:
    counts = OrderedDict((k, 0) for k in ("s-overdue", "s-today", "s-upcoming", "s-nodate", "s-done"))
    names = {"s-overdue": "overdue", "s-today": "due today", "s-upcoming": "upcoming",
             "s-nodate": "no date", "s-done": "done"}
    for note in notes:
        counts[_status(note, now)[0]] += 1
    total = f'<li class="chip"><strong>{len(notes)}</strong> note{"s" if len(notes) != 1 else ""}</li>'
    items = "".join(
        f'<li class="{css}"><strong>{n}</strong> {names[css]}</li>' for css, n in counts.items() if n
    )
    return f'<ul class="stats">{total}{items}</ul>'


def render_board(notes: List[Dict], now: datetime, label: Optional[str] = None,
                 standalone: bool = True) -> str:
    """Build the board. `label` names the range shown, for example 'Next 2 days'."""
    label = label or "All open notes"
    today = now.date()
    if notes:
        body = _stats(notes, now)
        for group in _group(notes, today).values():
            items = "".join(_note_html(n, now) for n in group["notes"])
            body += (
                f'<section class="day {group["css"]}">'
                f'<h2>{escape(group["title"])} <span class="n">{len(group["notes"])}</span></h2>'
                f'<ul class="notes">{items}</ul></section>'
            )
    else:
        body = (
            '<div class="empty"><strong>Nothing here</strong>'
            f"No notes found for {escape(label)}.</div>"
        )
    head = f"<title>{TITLE}</title>\n<style>{STYLE}</style>\n"
    main = (
        '<main class="board"><header>'
        f'<h1><span>●</span> {TITLE}</h1><p class="range">{escape(label)}</p></header>'
        f"{body}"
        f'<footer>Made {now:%a} {now.day} {now:%b %H:%M} from your Notemind notes. '
        "Notes added or finished later will not appear until you make the board again."
        "</footer></main>"
    )
    if not standalone:
        return head + main
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"{head}</head>\n<body>\n{main}\n</body>\n</html>\n"
    )
