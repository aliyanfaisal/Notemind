"""Find a due date and time inside free text. Rules only: no AI, no network."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import List, NamedTuple, Optional

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12, "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4,
    "saturday": 5, "sunday": 6,
}
# Short forms are also common English words ("sat", "sun", "wed"), so they only
# count after a cue such as "on", "by", "next" or "this".
WEEKDAY_SHORT = {
    "mon": 0, "tue": 1, "tues": 1, "wed": 2, "thu": 3, "thur": 3, "thurs": 3,
    "fri": 4, "sat": 5, "sun": 6,
}


def _alt(names) -> str:
    return "|".join(sorted(names, key=len, reverse=True))


_MONTH = _alt(MONTHS)
_DAY = r"(\d{1,2})(?:st|nd|rd|th)?"
_FLAGS = re.IGNORECASE

ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?\b")
DAY_FIRST_RE = re.compile(
    rf"\b(?:on\s+)?{_DAY}\s+({_MONTH})\b(?:\s*,?\s*(\d{{4}})\b)?", _FLAGS)
MONTH_FIRST_RE = re.compile(
    rf"\b(?:on\s+)?({_MONTH})\s+{_DAY}(?!\d)(?:\s*,?\s*(\d{{4}})\b)?", _FLAGS)
RELATIVE_RE = re.compile(r"\b(day after tomorrow|tomorrow|today)\b", _FLAGS)
IN_N_RE = re.compile(  # "in 2 hours", "in the next 2 hours", "within 3 days", "in an hour"
    r"\b(?:in|within)\s+(?:the\s+)?(?:next\s+)?(\d+|an?)\s+(minutes?|mins?|hours?|hrs?|days?|weeks?)\b",
    _FLAGS)
WEEKDAY_RE = re.compile(rf"\b(?:(next|this)\s+)?({_alt(WEEKDAYS)})\b", _FLAGS)
WEEKDAY_SHORT_RE = re.compile(
    rf"\b(on|by|next|this)\s+({_alt(WEEKDAY_SHORT)})\b", _FLAGS)
# 22/09, 22/09/2026, 22.09.26, 22-09-2026. Letters, digits and separators may
# not touch it, so ISO dates, versions (v1.2.3) and "24h" are left alone.
NUMERIC_RE = re.compile(r"(?<![\w./-])(\d{1,2})([/.-])(\d{1,2})(?:\2(\d{4}|\d{2}))?(?!\d)")
TIME_12H_RE = re.compile(r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", _FLAGS)
TIME_24H_RE = re.compile(r"\b(?:at\s+)?([01]?\d|2[0-3]):([0-5]\d)\b", _FLAGS)
NOON_RE = re.compile(r"\b(?:at\s+)?noon\b", _FLAGS)


@dataclass
class ParsedDue:
    due: str  # "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM"
    matched: str  # the words the date was read from
    assumptions: List[str] = field(default_factory=list)


class _Hit(NamedTuple):
    start: int
    end: int
    day: date
    at: Optional[time]
    notes: List[str]
    has_own_time: bool = False  # "in 2 hours" already carries a time


def _month_day(month: int, day: int, year: Optional[int], today: date, notes: List[str]):
    """Build a date; a year-less date that already passed means next year."""
    try:
        found = date(year or today.year, month, day)
        if year is None and found < today:
            found = date(today.year + 1, month, day)
            notes.append(f"{found:%d %b} has already passed this year, so I used {found.year}")
        elif year is not None and found < today:
            notes.append("that date is in the past")
        return found
    except ValueError:  # 31 Sep, 29 Feb in a non-leap year
        return None


def _weekday_date(target: int, qualifier: str, today: date, notes: List[str]) -> date:
    qualifier = qualifier.lower()
    ahead = (target - today.weekday()) % 7
    if qualifier == "next":  # that weekday in the following Monday-to-Sunday week
        return today + timedelta(days=7 - today.weekday() + target)
    if qualifier == "this":
        return today + timedelta(days=ahead)
    if ahead == 0:
        notes.append("today is that weekday, so I used next week")
        ahead = 7
    return today + timedelta(days=ahead)


def _numeric_hits(text: str, today: date, order: str) -> List[_Hit]:
    """Dates like 22/09. When both parts could be a month, `order` decides."""
    hits: List[_Hit] = []
    for m in NUMERIC_RE.finditer(text):
        first, sep, second = int(m[1]), m[2], int(m[3])
        if m[4] is None and sep != "/":
            continue  # "1.5" and "4-5" are far more likely numbers than dates
        year = None
        if m[4]:
            year = int(m[4]) + (2000 if len(m[4]) == 2 else 0)
        ambiguous = False
        if first > 12 and second <= 12:
            day, month = first, second
        elif second > 12 and first <= 12:
            month, day = first, second
        elif first <= 12 and second <= 12:
            day, month = (first, second) if order == "dmy" else (second, first)
            ambiguous = first != second
        else:
            continue
        notes: List[str] = []
        found = _month_day(month, day, year, today, notes)
        if not found:
            continue
        if ambiguous:
            other = _month_day(day, month, year, today, [])
            label = "day/month" if order == "dmy" else "month/day"
            switch = "mdy" if order == "dmy" else "dmy"
            notes.append(
                f"read {m[0]} as {label}: {found:%a %d %b %Y}. If you meant "
                f"{other:%a %d %b %Y}, write the month name or set NOTESCOS_DATE_ORDER={switch}"
            )
        hits.append(_Hit(m.start(), m.end(), found, None, notes))
    return hits


def _date_hits(text: str, now: datetime, order: str = "dmy") -> List[_Hit]:
    today = now.date()
    hits: List[_Hit] = []

    for m in ISO_RE.finditer(text):
        try:
            day = date(int(m[1]), int(m[2]), int(m[3]))
            at = time(int(m[4]), int(m[5])) if m[4] else None
        except ValueError:
            continue
        hits.append(_Hit(m.start(), m.end(), day, at, [], has_own_time=at is not None))

    hits.extend(_numeric_hits(text, today, order))

    for m in DAY_FIRST_RE.finditer(text):
        notes: List[str] = []
        day = _month_day(MONTHS[m[2].lower()], int(m[1]), int(m[3]) if m[3] else None, today, notes)
        if day:
            hits.append(_Hit(m.start(), m.end(), day, None, notes))

    for m in MONTH_FIRST_RE.finditer(text):
        notes = []
        day = _month_day(MONTHS[m[1].lower()], int(m[2]), int(m[3]) if m[3] else None, today, notes)
        if day:
            hits.append(_Hit(m.start(), m.end(), day, None, notes))

    for m in RELATIVE_RE.finditer(text):
        offset = {"today": 0, "tomorrow": 1, "day after tomorrow": 2}[m[1].lower()]
        hits.append(_Hit(m.start(), m.end(), today + timedelta(days=offset), None, []))

    for m in IN_N_RE.finditer(text):
        amount, unit = (1 if m[1].lower() in ('a', 'an') else int(m[1])), m[2].lower()
        if unit.startswith(("day", "week")):
            days = amount * (7 if unit.startswith("week") else 1)
            hits.append(_Hit(m.start(), m.end(), today + timedelta(days=days), None, []))
        else:
            delta = timedelta(hours=amount) if unit.startswith(("hour", "hr")) else timedelta(minutes=amount)
            later = (now + delta).replace(second=0, microsecond=0)
            hits.append(_Hit(m.start(), m.end(), later.date(), later.time(), [], has_own_time=True))

    for m in WEEKDAY_RE.finditer(text):
        notes = []
        day = _weekday_date(WEEKDAYS[m[2].lower()], m[1] or "", today, notes)
        hits.append(_Hit(m.start(), m.end(), day, None, notes))

    for m in WEEKDAY_SHORT_RE.finditer(text):
        notes = []
        cue = m[1].lower()
        day = _weekday_date(WEEKDAY_SHORT[m[2].lower()], cue if cue in ("next", "this") else "", today, notes)
        hits.append(_Hit(m.start(), m.end(), day, None, notes))

    return hits


def _find_time(text: str):
    """Return (time, matched words) for the first time of day in the text."""
    m = TIME_12H_RE.search(text)
    if m:
        hour, minute = int(m[1]), int(m[2] or 0)
        if 1 <= hour <= 12 and minute < 60:
            hour = hour % 12 + (12 if m[3].lower() == "pm" else 0)
            return time(hour, minute), m[0]
    m = TIME_24H_RE.search(text)
    if m:
        return time(int(m[1]), int(m[2])), m[0]
    m = NOON_RE.search(text)
    if m:
        return time(12, 0), m[0]
    return None


def parse_due(
    text: str, now: Optional[datetime] = None, date_order: str = "dmy"
) -> Optional[ParsedDue]:
    """Read a due date/time from text like "Call Sara on 22 sep at 3pm".

    Returns None when the text holds no date or time. Whenever a guess was
    needed (a year, a weekday that is today, a time already past) it is listed
    in `assumptions` so the caller can show it to the user. `date_order` says
    how to read 03/04: "dmy" (3 April) or "mdy" (March 4).
    """
    if date_order not in ("dmy", "mdy"):
        raise ValueError("date_order must be 'dmy' or 'mdy'")
    now = now or datetime.now()
    hits = _date_hits(text, now, date_order)
    spoken_time = None if any(h.has_own_time for h in hits) else _find_time(text)

    if hits:
        hit = min(hits, key=lambda h: h.start)
        at, matched, notes = hit.at, text[hit.start:hit.end].strip(), list(hit.notes)
        if at is None and spoken_time:
            at = spoken_time[0]
            matched += f" {spoken_time[1].strip()}"
        day = hit.day
    elif spoken_time:  # a time with no date: today, or tomorrow if it has passed
        at, matched, notes = spoken_time[0], spoken_time[1].strip(), []
        day = now.date()
        if datetime.combine(day, at) <= now:
            day += timedelta(days=1)
            notes.append("that time has already passed today, so I used tomorrow")
    else:
        return None

    due = day.isoformat() if at is None else datetime.combine(day, at).isoformat(timespec="minutes")
    return ParsedDue(due=due, matched=matched, assumptions=notes)
