"""Find sensitive data in note text and mask it with asterisks. Rules only: no AI, no network.

Used whenever note text is about to leave the machine or reach Claude: the startup
banner context, the Claude artifact board, and the skills' output. Your stored notes
are never changed. Detection is pattern based, so it catches common secrets and
identifiers, not everything. See the README for what is covered.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

MASK = "*****"
_FLAGS = re.IGNORECASE

# (kind, pattern, group). With group 0 the whole match is masked, otherwise just that group,
# so "password is hunter2" keeps its label and only the value is hidden.
_PATTERNS: List[Tuple[str, "re.Pattern[str]", int]] = [
    ("private key", re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)"), 0),
    ("API key", re.compile(
        r"\b(?:sk-ant-[\w-]{10,}|sk-[A-Za-z0-9_-]{16,}|[sr]k_(?:live|test)_\w{16,}"
        r"|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,}|glpat-[\w-]{15,}|npm_[A-Za-z0-9]{30,}"
        r"|AKIA[0-9A-Z]{16}|xox[abprs]-[\w-]{10,}|AIza[0-9A-Za-z_-]{30,})"), 0),
    ("token", re.compile(r"\beyJ[\w-]{8,}\.[\w-]{8,}\.[\w-]{8,}"), 0),
    ("token", re.compile(r"\bBearer\s+([A-Za-z0-9._~+/=-]{16,})", _FLAGS), 1),
    ("password in a link", re.compile(r"(?<=://)[^\s/:@]+:([^\s/@]+)(?=@)"), 1),
    ("password or secret", re.compile(
        r"\b(?:password|passwd|pwd|passcode|secret|token|api[ _-]?key|pin|otp|cvv|cvc)\b"
        r"(?:\s*[:=]\s*|\s+is\s+)([^\s,;]+)", _FLAGS), 1),
    ("code", re.compile(r"\b(?:otp|pin|cvv|cvc)\s+(\d{3,8})\b", _FLAGS), 1),
    ("social security number", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), 0),
    ("email address", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"), 0),
    ("phone number", re.compile(r"(?<![\w+])\+\d{1,3}[\s.-]?\(?\d{1,4}\)?(?:[\s.-]?\d{2,4}){2,4}\b"), 0),
]
_CARD_RE = re.compile(r"(?<![\d-])(?:\d[ -]?){12,18}\d(?![\d-])")
_IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,3})?\b")


def _luhn(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2:
            n = n * 2 - 9 if n > 4 else n * 2
        total += n
    return total % 10 == 0


def _iban_ok(value: str) -> bool:
    flat = re.sub(r"\s", "", value).upper()
    if not 15 <= len(flat) <= 34:
        return False
    moved = flat[4:] + flat[:4]
    return int("".join(str(int(c, 36)) for c in moved)) % 97 == 1


def find_sensitive(text: str) -> List[Tuple[int, int, str]]:
    """Return (start, end, kind) for each sensitive span, overlaps merged."""
    spans: List[Tuple[int, int, str]] = []
    for kind, pattern, group in _PATTERNS:
        for m in pattern.finditer(text):
            if m.start(group) >= 0:
                spans.append((m.start(group), m.end(group), kind))
    for m in _CARD_RE.finditer(text):
        digits = re.sub(r"\D", "", m[0])
        if 13 <= len(digits) <= 19 and _luhn(digits):
            spans.append((m.start(), m.end(), "card number"))
    for m in _IBAN_RE.finditer(text):
        if _iban_ok(m[0]):
            spans.append((m.start(), m.end(), "bank account number"))
    spans.sort()
    merged: List[Tuple[int, int, str]] = []
    for start, end, kind in spans:
        if merged and start < merged[-1][1]:
            prev = merged[-1]
            merged[-1] = (prev[0], max(prev[1], end), prev[2])
        else:
            merged.append((start, end, kind))
    return merged


def redact(text: Optional[str]) -> Tuple[Optional[str], List[str]]:
    """Mask sensitive data. Returns (masked text, kinds found)."""
    if not text:
        return text, []
    spans = find_sensitive(text)
    if not spans:
        return text, []
    out, last = [], 0
    for start, end, _ in spans:
        out.append(text[last:start])
        out.append(MASK)
        last = end
    out.append(text[last:])
    return "".join(out), [kind for _, _, kind in spans]


def redact_note(note: Dict) -> Tuple[Dict, int]:
    """A copy of a note with its free-text fields masked, and how many items were masked."""
    masked, count = dict(note), 0
    for field in ("text", "person", "project"):
        masked[field], found = redact(note.get(field))
        count += len(found)
    tags = []
    for tag in note.get("tags") or []:
        value, found = redact(tag)
        tags.append(value)
        count += len(found)
    masked["tags"] = tags
    return masked, count


def redact_notes(notes: List[Dict]) -> Tuple[List[Dict], int]:
    results = [redact_note(n) for n in notes]
    return [n for n, _ in results], sum(c for _, c in results)
