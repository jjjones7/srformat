"""Normalize messy spaced-repetition schedule records into a canonical form.

Every review-log export we've seen (Anki CSV dumps, Mnemosyne backups,
hand-rolled spreadsheets) spells dates, intervals, ease factors and grades
differently. This module turns one raw line into a NormalizedRecord with a
fixed shape: ISO date, integer days, a 1.30-ish float ease, and a 0-3 rating.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

FIELD_SPLIT = re.compile(r"[|,;\t]")

DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%b %d %Y",
    "%B %d, %Y",
]

# Interval units, longest strings first so "months" doesn't get eaten by "mo".
INTERVAL_UNITS = [
    ("years", 365), ("year", 365), ("yrs", 365), ("yr", 365), ("y", 365),
    ("months", 30), ("month", 30), ("mos", 30), ("mo", 30),
    ("weeks", 7), ("week", 7), ("wks", 7), ("wk", 7), ("w", 7),
    ("days", 1), ("day", 1), ("d", 1),
]

ISO_DURATION_RE = re.compile(r"^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?$", re.IGNORECASE)

RATING_ALIASES = {
    "again": 0, "fail": 0, "failed": 0, "wrong": 0, "forgot": 0, "0": 0,
    "hard": 1, "difficult": 1, "1": 1,
    "good": 2, "pass": 2, "passed": 2, "ok": 2, "okay": 2, "2": 2,
    "easy": 3, "perfect": 3, "3": 3,
}
RATING_LABELS = ["again", "hard", "good", "easy"]


class ParseError(ValueError):
    """Raised when a raw record or field can't be made sense of."""


@dataclass
class NormalizedRecord:
    due: date
    interval_days: int
    ease: float
    rating: int

    @property
    def rating_label(self) -> str:
        return RATING_LABELS[self.rating]

    def as_row(self) -> tuple[str, str, str, str]:
        return (
            self.due.isoformat(),
            str(self.interval_days),
            f"{self.ease:.2f}",
            self.rating_label,
        )


def split_fields(line: str) -> list[str]:
    fields = [f.strip() for f in FIELD_SPLIT.split(line)]
    fields = [f for f in fields if f != ""]
    if len(fields) != 4:
        raise ParseError(
            f"expected 4 fields (due, interval, ease, rating), got {len(fields)}: {line!r}"
        )
    return fields


def normalize_date(raw: str) -> date:
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ParseError(f"unrecognized date: {raw!r}")


def normalize_interval(raw: str) -> int:
    raw = raw.strip()
    iso = ISO_DURATION_RE.match(raw)
    if iso and raw.upper() != "P":
        years, months, days = (int(g) if g else 0 for g in iso.groups())
        total = years * 365 + months * 30 + days
        if total <= 0:
            raise ParseError(f"interval must be positive: {raw!r}")
        return total

    match = re.match(r"^(\d+(?:\.\d+)?)\s*([a-zA-Z]*)$", raw)
    if not match:
        raise ParseError(f"unrecognized interval: {raw!r}")
    amount, unit = match.groups()
    unit = unit.lower()
    multiplier = 1
    if unit:
        for name, days_per_unit in INTERVAL_UNITS:
            if unit == name:
                multiplier = days_per_unit
                break
        else:
            raise ParseError(f"unrecognized interval unit: {unit!r} in {raw!r}")
    total_days = round(float(amount) * multiplier)
    if total_days <= 0:
        raise ParseError(f"interval must be positive: {raw!r}")
    return total_days


def normalize_ease(raw: str) -> float:
    raw = raw.strip()
    is_percent = raw.endswith("%")
    if is_percent:
        raw = raw[:-1].strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise ParseError(f"unrecognized ease factor: {raw!r}") from exc
    if is_percent or value > 10:
        # "250" or "250%" both mean 2.50 - nobody exports an ease factor
        # above 10 as a plain multiplier, so treat it as percent-scaled.
        value = value / 100
    if value <= 0:
        raise ParseError(f"ease factor must be positive: {raw!r}")
    return value


def normalize_rating(raw: str) -> int:
    key = raw.strip().lower()
    if key not in RATING_ALIASES:
        raise ParseError(f"unrecognized rating: {raw!r}")
    return RATING_ALIASES[key]


def normalize_record(line: str) -> NormalizedRecord:
    due_raw, interval_raw, ease_raw, rating_raw = split_fields(line)
    return NormalizedRecord(
        due=normalize_date(due_raw),
        interval_days=normalize_interval(interval_raw),
        ease=normalize_ease(ease_raw),
        rating=normalize_rating(rating_raw),
    )
