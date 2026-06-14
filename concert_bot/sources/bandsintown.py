"""Bandsintown source — uses Bandsintown's official Events REST API.

Docs (unofficial but widely used): https://rest-api.bandsintown.com

For each tracked artist we call:

    GET https://rest-api.bandsintown.com/artists/{artist}/events
        ?app_id={BANDSINTOWN_APP_ID}&date=upcoming

This returns a JSON array of upcoming events for that artist worldwide.
This source provides no presale information — only Ticketmaster does.

Because this depends on an external API and an app id that could be
revoked or rate-limited, every step is wrapped so that a failure for one
artist (or all artists) is logged as a warning and never crashes the run.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import requests

from concert_bot.config import Config
from concert_bot.models import Event
from concert_bot.sources.base import Source

log = logging.getLogger(__name__)

SOURCE_NAME = "bandsintown"

BASE_URL = "https://rest-api.bandsintown.com"


class BandsintownSource(Source):
    name = SOURCE_NAME

    def __init__(self, config: Config):
        self.app_id = config.bandsintown_app_id
        self.request_delay = config.bandsintown.request_delay_seconds
        self.max_retries = config.bandsintown.max_retries

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def fetch_events(self, artist_to_lists: dict[str, set[str]]) -> list[Event]:
        events: list[Event] = []

        if not self.app_id:
            log.warning("Bandsintown: BANDSINTOWN_APP_ID not set — skipping")
            return []

        for artist, matched_lists in artist_to_lists.items():
            try:
                raw_events = self._fetch_artist_events(artist)
            except Exception as exc:
                log.warning("Bandsintown: failed to fetch events for %r: %s", artist, exc)
                time.sleep(self.request_delay)
                continue

            for raw_event in raw_events or []:
                try:
                    event = _parse_event(raw_event, artist, matched_lists)
                except Exception as exc:
                    log.warning("Bandsintown: failed to parse event for %r: %s", artist, exc)
                    continue
                if event:
                    events.append(event)

            time.sleep(self.request_delay)

        log.info("Bandsintown: fetched %d event(s)", len(events))
        return events

    def _fetch_artist_events(self, artist: str) -> list[dict] | None:
        """GET the upcoming events for an artist, with retries/backoff."""
        url = f"{BASE_URL}/artists/{requests.utils.quote(artist, safe='')}/events"
        params = {"app_id": self.app_id, "date": "upcoming"}

        delay = self.request_delay
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(url, params=params, timeout=20)
            except requests.RequestException as exc:
                if attempt == self.max_retries:
                    raise
                log.warning(
                    "Bandsintown: request error fetching events for %r (attempt %d/%d): %s — retrying",
                    artist, attempt, self.max_retries, exc,
                )
                time.sleep(delay)
                delay *= 2
                continue

            if resp.status_code == 404:
                log.warning("Bandsintown: no artist found for %r (404)", artist)
                return None

            if resp.status_code == 429:
                if attempt == self.max_retries:
                    log.warning("Bandsintown: rate limited fetching events for %r — giving up", artist)
                    return None
                log.warning(
                    "Bandsintown: rate limited (429) fetching events for %r — backing off %.1fs",
                    artist, delay,
                )
                time.sleep(delay)
                delay *= 2
                continue

            resp.raise_for_status()
            data = resp.json()

            if isinstance(data, dict):
                log.warning(
                    "Bandsintown: unexpected response for %r: %s",
                    artist, data.get("errorMessage", data),
                )
                return None

            return data

        return None


def _parse_event(raw: dict, artist: str, matched_lists: set[str]) -> Event | None:
    venue = raw.get("venue", {})
    event_dt = _parse_datetime(raw.get("datetime"))
    onsale_dt = _parse_datetime(raw.get("on_sale_datetime"))

    url = raw.get("url", "")
    if not url:
        offers = raw.get("offers") or []
        if offers and isinstance(offers, list):
            url = offers[0].get("url", "")

    return Event(
        artist=artist,
        event_name=raw.get("title") or artist,
        venue=venue.get("name", ""),
        city=venue.get("city", ""),
        country=_country_code(venue.get("country", "")),
        event_date=event_dt.date() if event_dt else None,
        event_time=event_dt.strftime("%H:%M") if event_dt else None,
        onsale_datetime=onsale_dt,
        presales=[],
        source=SOURCE_NAME,
        url=url,
        matched_lists=set(matched_lists),
    )


def _parse_datetime(value: str | None) -> datetime | None:
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


# Bandsintown sometimes gives full country names instead of codes.
_COUNTRY_NAME_TO_CODE = {
    "united kingdom": "GB",
    "uk": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "northern ireland": "GB",
    "spain": "ES",
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
}


def _country_code(country: str) -> str:
    if not country:
        return ""
    if len(country) == 2:
        return country.upper()
    return _COUNTRY_NAME_TO_CODE.get(country.strip().lower(), country)
