"""Normalized data models shared by every source."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class Presale:
    """A single presale window (e.g. 'Citi Card Presale')."""

    name: str
    start: datetime | None
    end: datetime | None


@dataclass
class Event:
    """A single concert/show announcement, normalized across sources."""

    artist: str
    event_name: str
    venue: str
    city: str
    country: str  # ISO 3166-1 alpha-2 code, e.g. "GB", "ES", "US"
    event_date: date | None
    event_time: str | None  # local venue time, e.g. "19:30", or None if unknown
    onsale_datetime: datetime | None
    presales: list[Presale]
    source: str
    url: str
    matched_lists: set[str] = field(default_factory=set)

    @property
    def canonical_key(self) -> str:
        """Key used for deduplication: normalized artist + event date (day) + city."""
        artist_part = normalize_text(self.artist)
        city_part = normalize_text(self.city)
        date_part = self.event_date.isoformat() if self.event_date else "unknown-date"
        return f"{artist_part}|{date_part}|{city_part}"


@dataclass
class MergedEvent:
    """The result of merging one or more duplicate Events from different sources."""

    artist: str
    event_name: str
    venue: str
    city: str
    country: str
    event_date: date | None
    event_time: str | None
    onsale_datetime: datetime | None
    presales: list[Presale]
    sources: list[str]
    urls: list[tuple[str, str]]  # (source_name, url)
    matched_lists: set[str]
    priority: bool = False

    @property
    def canonical_key(self) -> str:
        artist_part = normalize_text(self.artist)
        city_part = normalize_text(self.city)
        date_part = self.event_date.isoformat() if self.event_date else "unknown-date"
        return f"{artist_part}|{date_part}|{city_part}"


def normalize_text(text: str) -> str:
    """Lowercase, strip accents/punctuation, collapse whitespace."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def venue_similarity(venue_a: str, venue_b: str) -> float:
    """Light fuzzy match ratio (0.0-1.0) between two venue names."""
    from difflib import SequenceMatcher

    a = normalize_text(venue_a)
    b = normalize_text(venue_b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()
