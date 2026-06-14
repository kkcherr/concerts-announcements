"""Bandsintown source — scrapes the JSON embedded in artist pages.

Bandsintown does not offer a usable public API for tracking many artists
(the official REST API requires a registered app_id and is heavily
rate-limited), so instead we fetch each tracked artist's public page at
bandsintown.com and parse the JSON payload the page itself loads
(a Next.js `__NEXT_DATA__` blob containing the artist's upcoming events).

This source provides no presale information.

Because this relies on Bandsintown's page structure, which can change at
any time without notice, every step is wrapped so that a failure for one
artist (or all artists) is logged as a warning and never crashes the run.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone

import requests

from concert_bot.config import Config
from concert_bot.models import Event
from concert_bot.sources.base import Source

log = logging.getLogger(__name__)

SOURCE_NAME = "bandsintown"

BASE_URL = "https://www.bandsintown.com/a/{slug}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}

NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.DOTALL,
)


class BandsintownSource(Source):
    name = SOURCE_NAME

    def __init__(self, config: Config):
        self.request_delay = config.bandsintown.request_delay_seconds
        self.max_retries = config.bandsintown.max_retries

    def fetch_events(self, artist_to_lists: dict[str, set[str]]) -> list[Event]:
        events: list[Event] = []

        for artist, matched_lists in artist_to_lists.items():
            try:
                page_data = self._fetch_artist_page(artist)
            except Exception as exc:
                log.warning("Bandsintown: failed to fetch page for %r: %s", artist, exc)
                time.sleep(self.request_delay)
                continue

            if page_data is None:
                time.sleep(self.request_delay)
                continue

            try:
                if not _validate_artist_page(page_data, artist):
                    log.warning(
                        "Bandsintown: page for %r doesn't look like a valid artist page — skipping",
                        artist,
                    )
                    time.sleep(self.request_delay)
                    continue

                raw_events = _extract_events(page_data)
            except Exception as exc:
                log.warning("Bandsintown: failed to parse page for %r: %s", artist, exc)
                time.sleep(self.request_delay)
                continue

            for raw_event in raw_events:
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

    def _fetch_artist_page(self, artist: str) -> dict | None:
        slug = _slugify(artist)
        url = BASE_URL.format(slug=slug)

        delay = self.request_delay
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(url, headers=HEADERS, timeout=20)
            except requests.RequestException as exc:
                if attempt == self.max_retries:
                    raise
                log.warning(
                    "Bandsintown: request error for %r (attempt %d/%d): %s — retrying",
                    artist, attempt, self.max_retries, exc,
                )
                time.sleep(delay)
                delay *= 2
                continue

            if resp.status_code == 429:
                if attempt == self.max_retries:
                    log.warning("Bandsintown: rate limited for %r — giving up", artist)
                    return None
                log.warning(
                    "Bandsintown: rate limited (429) for %r — backing off %.1fs",
                    artist, delay,
                )
                time.sleep(delay)
                delay *= 2
                continue

            if resp.status_code == 404:
                log.warning("Bandsintown: no page found for %r (404)", artist)
                return None

            resp.raise_for_status()
            return _parse_next_data(resp.text)

        return None


def _slugify(artist: str) -> str:
    slug = artist.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _parse_next_data(html: str) -> dict | None:
    match = NEXT_DATA_RE.search(html)
    if not match:
        log.warning("Bandsintown: __NEXT_DATA__ block not found in page (site layout may have changed)")
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        log.warning("Bandsintown: __NEXT_DATA__ block is not valid JSON: %s", exc)
        return None


def _validate_artist_page(page_data: dict, artist: str) -> bool:
    """Confirm the page actually belongs to the artist we asked for."""
    artist_info = _find_first(page_data, lambda d: "name" in d and ("upcomingEventCount" in d or "url" in d))
    if not artist_info:
        return False
    page_name = str(artist_info.get("name", "")).strip().lower()
    return page_name == artist.strip().lower() or artist.strip().lower() in page_name


def _extract_events(page_data: dict) -> list[dict]:
    """Recursively find event-like dicts: objects with 'datetime' and 'venue' keys."""
    results: list[dict] = []
    _collect_events(page_data, results)
    return results


def _collect_events(node, results: list[dict]) -> None:
    if isinstance(node, dict):
        if "datetime" in node and "venue" in node and isinstance(node["venue"], dict):
            results.append(node)
            return
        for value in node.values():
            _collect_events(value, results)
    elif isinstance(node, list):
        for item in node:
            _collect_events(item, results)


def _find_first(node, predicate):
    if isinstance(node, dict):
        if predicate(node):
            return node
        for value in node.values():
            found = _find_first(value, predicate)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_first(item, predicate)
            if found is not None:
                return found
    return None


def _parse_event(raw: dict, artist: str, matched_lists: set[str]) -> Event | None:
    venue = raw.get("venue", {})
    event_dt = _parse_datetime(raw.get("datetime"))

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
        onsale_datetime=None,
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
