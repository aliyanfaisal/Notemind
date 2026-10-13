"""Read money out of a note: who owes whom, how much, in what currency. Rules only, no AI.

"Ali owes me 15k, due Friday"  -> money_owed (someone owes you), Ali, 15000
"I owe Sara $200"              -> money_due (you owe), Sara, 200 USD
Only text that clearly talks about owing or paying becomes a money note; everything
else stays a plain note, so a stray number is never mistaken for an amount.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

_FLAGS = re.IGNORECASE

SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP", "₹": "INR"}
WORDS = {
    "usd": "USD", "dollar": "USD", "dollars": "USD", "bucks": "USD",
    "eur": "EUR", "euro": "EUR", "euros": "EUR", "gbp": "GBP", "pounds": "GBP",
    "pkr": "PKR", "rs": "PKR", "rupee": "PKR", "rupees": "PKR",
    "inr": "INR", "aed": "AED", "dirham": "AED", "dirhams": "AED",
    "cad": "CAD", "aud": "AUD", "sar": "SAR",
}
SCALE = {"k": 1_000, "thousand": 1_000, "m": 1_000_000, "mn": 1_000_000, "million": 1_000_000,
         "lakh": 100_000, "lac": 100_000, "lakhs": 100_000, "crore": 10_000_000}

_NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
_SCALE = r"(?:\s?(?:k|thousand|m|mn|million|lakhs?|lacs?|crore)\b)"
_CODES = "|".join(sorted(WORDS, key=len, reverse=True))
_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*"

# Candidates, most specific first. Group names: sym / pre (code before) / num / scale / post.
_AMOUNT_RES = [
    re.compile(rf"(?P<sym>[$€£₹])\s?(?P<num>{_NUM})(?P<scale>{_SCALE})?", _FLAGS),
    re.compile(rf"\b(?P<pre>{_CODES})\.?\s?(?P<num>{_NUM})(?P<scale>{_SCALE})?", _FLAGS),
    re.compile(rf"(?<![\w.])(?P<num>{_NUM})(?P<scale>{_SCALE})?\s?(?P<post>{_CODES})\b", _FLAGS),
    re.compile(rf"(?<![\w.$€£₹])(?P<num>{_NUM})(?P<scale>{_SCALE})(?![\w])", _FLAGS),
]
_BARE_RE = re.compile(rf"(?<![\w.:/-])(?P<num>{_NUM})(?![\w:/-])")
# A bare number after "owes" is only an amount if it is not part of a date or time.
_NOT_AMOUNT_AFTER = re.compile(rf"\s*(?:{_MONTH}|am|pm|st|nd|rd|th|o'clock|days?|hours?|mins?)\b", _FLAGS)
_NOT_AMOUNT_BEFORE = re.compile(r"\b(?:on|at|by|the|in|for)\s*$", _FLAGS)

_OWED_TO_ME = re.compile(
    r"\b(?P<who>[A-Za-z][\w'-]*)\s+(?:still\s+)?(?:owes?|owed)\s+me\b"
    r"|\b(?:owes?|owed)\s+(?:to\s+)?me\b|\bpay(?:s|ing)?\s+me\b|\b(?:i\s+)?(?:lent|lend)\s+(?P<lent>[A-Za-z][\w'-]*)"
    r"|\bi(?:'m| am)\s+owed\b|\bpay\s+me\s+back\b", _FLAGS)
_I_OWE = re.compile(
    r"\bi\s+(?:still\s+)?owe\s+(?P<who>[A-Za-z][\w'-]*)|\bi\s+(?:need|have|must|should|got)\s+to\s+pay\s*(?P<who2>[A-Za-z][\w'-]*)?"
    r"|\b(?:pay|repay|send|transfer)\s+(?P<who3>[A-Za-z][\w'-]*)\b|\bowe\s+(?P<who4>[A-Za-z][\w'-]*)\b", _FLAGS)

_MONEY_WORD = re.compile(r"\b(?:money|cash|payment|loan|dues?|balance|rent|salary|fees?|back)\b", _FLAGS)
_NOT_NAMES = {
    "i", "me", "my", "he", "she", "they", "we", "you", "who", "it", "him", "her", "them", "us",
    "the", "a", "an", "to", "back", "for", "on", "by", "rent", "bill", "bills", "fee", "fees",
    "tax", "taxes", "invoice", "salary", "money", "cash", "now", "later", "soon", "still", "this",
    "that", "some", "all", "half", "first", "next", "dues", "due", "about", "from", "of", "in",
    "at", "and", "or", "is", "was", "will", "must", "need", "have", "still", "also", "just",
}


def _amount_from(match: "re.Match[str]") -> Tuple[float, Optional[str]]:
    number = float(match.group("num").replace(",", ""))
    scale = (match.groupdict().get("scale") or "").strip().lower()
    if scale:
        number *= SCALE[scale]
    currency = None
    groups = match.groupdict()
    if groups.get("sym"):
        currency = SYMBOLS[groups["sym"]]
    elif groups.get("pre"):
        currency = WORDS[groups["pre"].lower()]
    elif groups.get("post"):
        currency = WORDS[groups["post"].lower()]
    return (int(number) if number == int(number) else round(number, 2)), currency


def find_amount(text: str, bare_ok: bool = False) -> Optional[Tuple[float, Optional[str]]]:
    """(amount, currency) from the text, or None. A bare number such as "owes me 500" is
    accepted only when `bare_ok` says the text is already about owing or paying."""
    best = None
    for pattern in _AMOUNT_RES:
        for match in pattern.finditer(text):
            if best is None or match.start() < best.start():
                best = match
        if best is not None:
            return _amount_from(best)
    if bare_ok:
        for match in _BARE_RE.finditer(text):
            if _NOT_AMOUNT_AFTER.match(text, match.end()) or _NOT_AMOUNT_BEFORE.search(text[: match.start()]):
                continue
            if len(match.group("num").replace(",", "").split(".")[0]) == 4 and 1900 <= float(
                    match.group("num").replace(",", "")) <= 2100:
                continue  # looks like a year
            return _amount_from(match)
    return None


def _person(*candidates: Optional[str]) -> Optional[str]:
    for name in candidates:
        if name and name.lower() not in _NOT_NAMES:
            return name[:1].upper() + name[1:]
    return None


def read_money(text: str) -> Optional[Dict]:
    """What a note says about money, or None when it is not about money.

    Returns {"type": "money_owed"|"money_due", "amount", "currency", "person"}; amount,
    currency and person may be None when the text does not say.
    """
    mine = _OWED_TO_ME.search(text)
    owe = _I_OWE.search(text) if not mine else None
    if not mine and not owe:
        return None
    direct = bool(mine) or bool(re.search(r"\bowe\b", text, _FLAGS))
    found = find_amount(text, bare_ok=direct)
    if mine:
        if not found and not _MONEY_WORD.search(text):
            return None  # "Ali owes me a call" is about a favour, not money
        return {"type": "money_owed", "amount": found[0] if found else None,
                "currency": found[1] if found else None,
                "person": _person(mine.groupdict().get("who"), mine.groupdict().get("lent"))}
    if not found:  # "pay Sara" alone is an ordinary task, not a debt
        return None
    g = owe.groupdict()
    return {"type": "money_due", "amount": found[0], "currency": found[1],
            "person": _person(g.get("who"), g.get("who2"), g.get("who3"), g.get("who4"))}


def format_amount(amount: Optional[float], currency: Optional[str]) -> str:
    """15000 USD -> '15,000 USD'; None -> ''."""
    if amount is None:
        return ""
    number = f"{amount:,.2f}".rstrip("0").rstrip(".") if isinstance(amount, float) else f"{amount:,}"
    return f"{number} {currency}" if currency else number


def totals(notes: List[Dict], kind: str) -> Dict[Optional[str], float]:
    """Sum of open notes of one money type, per currency."""
    result: Dict[Optional[str], float] = {}
    for n in notes:
        if n["status"] == "open" and n["type"] == kind and n.get("amount") is not None:
            result[n["currency"]] = result.get(n["currency"], 0) + n["amount"]
    return result


def note_fields(text: str) -> Dict:
    """Fields to save with a note whose text is about money, or {} for an ordinary note."""
    found = read_money(text)
    if not found:
        return {}
    fields = {"type": found["type"]}
    for key in ("amount", "currency", "person"):
        if found[key] is not None:
            fields[key] = found[key]
    return fields
