"""Priority scoring. Plain arithmetic, so results are fast, free and explainable."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .brief import split_due, when_label

# Every weight can be overridden under "weights" in ~/.notescos/config.json.
DEFAULT_WEIGHTS: Dict[str, int] = {
    "overdue_base": 100, "overdue_per_day": 5, "overdue_cap": 150,
    "due_today": 90, "due_tomorrow": 70, "due_in_3_days": 50, "due_in_7_days": 25,
    "priority": 20,  # per user priority level (1 to 3)
    "urgent": 30,  # a note marked --alert urgent
    "type_money_owed": 15, "type_followup": 10, "type_waiting_on": 10, "type_task": 5,
    "stale_3_days": 15, "stale_7_days": 30,
}
FOLLOW_UP_TYPES = ("followup", "waiting_on")


def _days_untouched(note: Dict, now: datetime) -> int:
    """Whole days since a note was last changed (stored in UTC, compared in local time)."""
    changed = datetime.fromisoformat(note["updated_at"]).astimezone().replace(tzinfo=None)
    return max(0, (now - changed).days)


def stale_days(note: Dict, now: datetime, min_days: int = 3) -> Optional[int]:
    """Days a follow-up has gone untouched, or None if it is not a stale follow-up."""
    if note["status"] != "open" or note["type"] not in FOLLOW_UP_TYPES:
        return None
    days = _days_untouched(note, now)
    return days if days >= min_days else None


def is_alertable(note: Dict) -> bool:
    """Open, confirmed notes that are not marked silent. Snoozed, done, silent and
    still-unclear notes never alert."""
    return note["status"] == "open" and note["alert_level"] != "silent" and bool(note["confirmed"])


def score_note(note: Dict, now: datetime, weights: Optional[Dict[str, int]] = None) -> Tuple[int, str]:
    """Return (score, one-line reason) for an open note."""
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    score, why = 0, []
    if note["due_at"]:
        day, at = split_due(note["due_at"])
        today = now.date()
        if day < today or (day == today and at is not None and at <= now.time()):
            late = (today - day).days
            score += min(w["overdue_base"] + late * w["overdue_per_day"], w["overdue_cap"])
        elif day == today:
            score += w["due_today"]
        elif day == today + timedelta(days=1):
            score += w["due_tomorrow"]
        elif day <= today + timedelta(days=3):
            score += w["due_in_3_days"]
        elif day <= today + timedelta(days=7):
            score += w["due_in_7_days"]
        why.append(when_label(note, now))
    if note["priority"]:
        score += note["priority"] * w["priority"]
        why.append(f"priority {note['priority']}")
    if note["alert_level"] == "urgent":
        score += w["urgent"]
        why.append("urgent")
    score += w.get(f"type_{note['type']}", 0)
    waiting = stale_days(note, now)
    if waiting is not None:
        score += w["stale_7_days"] if waiting >= 7 else w["stale_3_days"]
        why.append(f"waiting {waiting}d")
    return score, " · ".join(why) or "no date"


def rank(notes: List[Dict], now: datetime, weights: Optional[Dict[str, int]] = None) -> List[Dict]:
    """Alertable notes, highest score first, each with 'score' and 'why' added."""
    ranked = []
    for note in notes:
        if is_alertable(note):
            score, why = score_note(note, now, weights)
            ranked.append({**note, "score": score, "why": why})
    ranked.sort(key=lambda n: (-n["score"], n["due_at"] is None, n["due_at"] or "", n["id"]))
    return ranked
