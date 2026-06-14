"""Ticketmaster Discovery API v2 source.

Docs: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/

This is the only source that exposes presale windows (via the
`sales.presales` array on each event), so it's treated as the primary
source. For each tracked artist we:

1. Resolve the artist name to a Ticketmaster `attractionId` via the
   /attractions endpoint (cached locally so we only do this once per artist).
2. Query /events with that attractionId and no location filter, so shows
   anywhere in the world are returned.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests

from concert_bot.config import Config
from concert_bot.models import Event, Presale
from concert_bot.sources.base import Source

log = logging.getLogger(__name__)

BASE_URL = "https://app.ticketmaster.com/discovery/v2"
SOURCE_NAME = "ticketmaster"


class TicketmasterSource(Source):
    name = SOURCE_NAME

    def __init__(self, config: Config):
        self.api_key = config.ticketmaster_api_key
        self.page_size = config.ticketmaster.events_page_size
        self.request_delay = config.ticketmaster.request_delay_seconds
        self.cache_path = Path(config.paths.ticketmaster_attraction_cache)
        self._cache = self._load_cache()

    # ------------------------------------------------------------------
    # Attraction ID cache
    # ------------------------------------------------------------------

    def _load_cache(self) -> dict[str, str | None]:
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                log.warning("Ticketmaster: failed to read attraction cache (%s)", exc)
        return {}

    def _save_cache(self) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, sort_keys=True)
        except OSError as exc:
            log.warning("Ticketmaster: failed to write attraction cache (%s)", exc)

    def _resolve_attraction_id(self, artist: str) -> str | None:
        cache_key = artist.strip().lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        attraction_id = self._lookup_attraction_id(artist)
        self._cache[cache_key] = attraction_id
        self._save_cache()
        return attraction_id

    def _lookup_attraction_id(self, artist: str) -> str | None:
        params = {
            "apikey": self.api_key,
            "keyword": artist,
            "classificationName": "music",
            "size": 20,
        }
        resp = requests.get(f"{BASE_URL}/attractions.json", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        attractions = data.get("_embedded", {}).get("attractions", [])
        if not attractions:
            log.warning("Ticketmaster: no attraction found for artist %r", artist)
            return None

        target = artist.strip().lower()
        for attraction in attractions:
            if attraction.get("name", "").strip().lower() == target:
                return attraction.get("id")

        # No exact match — fall back to the first result.
        return attractions[0].get("id")

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def fetch_events(self, artist_to_lists: dict[str, set[str]]) -> list[Event]:
        events: list[Event] = []

        for artist, matched_lists in artist_to_lists.items():
            if not self.api_key:
                log.warning("Ticketmaster: TICKETMASTER_API_KEY not set — skipping")
                return []

            try:
                attraction_id = self._resolve_attraction_id(artist)
            except Exception as exc:
                log.warning("Ticketmaster: failed to resolve attraction for %r: %s", artist, exc)
                continue

            if not attraction_id:
                continue

            try:
                raw_events = self._fetch_events_for_attraction(attraction_id)
            except Exception as exc:
                log.warning("Ticketmaster: failed to fetch events for %r: %s", artist, exc)
                continue

            for raw_event in raw_events:
                try:
                    event = self._parse_event(raw_event, artist, matched_lists)
                except Exception as exc:
                    log.warning(
                        "Ticketmaster: failed to parse event %r for %r: %s",
                        raw_event.get("id"), artist, exc,
                    )
                    continue
                if event:
                    events.append(event)

            time.sleep(self.request_delay)

        log.info("Ticketmaster: fetched %d event(s)", len(events))
        return events

    def _fetch_events_for_attraction(self, attraction_id: str) -> list[dict]:
        events: list[dict] = []
        page = 0
        while True:
            params = {
                "apikey": self.api_key,
                "attractionId": attraction_id,
                "size": self.page_size,
                "page": page,
                "sort": "date,asc",
            }
            resp = requests.get(f"{BASE_URL}/events.json", params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            page_events = data.get("_embedded", {}).get("events", [])
            events.extend(page_events)

            page_info = data.get("page", {})
            total_pages = page_info.get("totalPages", 1)
            page += 1
            if page >= total_pages:
                break

            time.sleep(self.request_delay)

        return events

    def _parse_event(
        self, raw: dict, artist: str, matched_lists: set[str]
    ) -> Event | None:
        venues = raw.get("_embedded", {}).get("venues", [])
        venue = venues[0] if venues else {}

        venue_name = venue.get("name", "")
        city = venue.get("city", {}).get("name", "")
        country = venue.get("country", {}).get("countryCode", "")

        dates = raw.get("dates", {})
        start = dates.get("start", {})
        event_date = _parse_date(start.get("localDate"))
        event_time = start.get("localTime")

        sales = raw.get("sales", {})
        onsale_datetime = _parse_datetime(sales.get("public", {}).get("startDateTime"))

        presales = [
            Presale(
                name=p.get("name", "Presale"),
                start=_parse_datetime(p.get("startDateTime")),
                end=_parse_datetime(p.get("endDateTime")),
            )
            for p in sales.get("presales", [])
        ]

        return Event(
            artist=artist,
            event_name=raw.get("name", artist),
            venue=venue_name,
            city=city,
            country=country,
            event_date=event_date,
            event_time=event_time,
            onsale_datetime=onsale_datetime,
            presales=presales,
            source=SOURCE_NAME,
            url=raw.get("url", ""),
            matched_lists=set(matched_lists),
        )


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse a UTC ISO8601 datetime like '2024-05-01T19:00:00Z'."""
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None
