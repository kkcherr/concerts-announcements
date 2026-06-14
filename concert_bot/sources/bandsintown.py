"""Bandsintown source — scrapes the JSON embedded in artist pages.

Bandsintown does not offer a usable public API for tracking many artists
(the official REST API requires a registered app_id and is heavily
rate-limited), so instead we:

1. Use Bandsintown's own search page to resolve an artist name to their
   canonical artist page URL (Bandsintown artist URLs include a numeric
   id, e.g. `/a/1837895-taylor-swift`, which can't be guessed from the
   name alone). This result is cached locally so we only search once per
   artist.
2. Fetch that artist page and parse the JSON payload the page itself loads
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
from difflib import SequenceMatcher
from pathlib import Path

import requests

from concert_bot.config import Config
from concert_bot.models import Event, normalize_text
from concert_bot.sources.base import Source

log = logging.getLogger(__name__)

SOURCE_NAME = "bandsintown"

SEARCH_URL = "https://www.bandsintown.com/search?q={query}"
ARTIST_URL_PREFIX = "https://www.bandsintown.com"

# How similar (0.0-1.0) a search result's name needs to be to the artist
# we're looking for, before we trust it's the right artist page.
NAME_MATCH_THRESHOLD = 0.85

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
        self.path_cache_path = Path(config.paths.bandsintown_artist_path_cache)
        self._path_cache = self._load_path_cache()

    # ------------------------------------------------------------------
    # Artist URL cache
    # ------------------------------------------------------------------

    def _load_path_cache(self) -> dict[str, str | None]:
        if self.path_cache_path.exists():
            try:
                with open(self.path_cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                log.warning("Bandsintown: failed to read artist URL cache (%s)", exc)
        return {}

    def _save_path_cache(self) -> None:
        try:
            self.path_cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path_cache_path, "w", encoding="utf-8") as f:
                json.dump(self._path_cache, f, indent=2, sort_keys=True)
        except OSError as exc:
            log.warning("Bandsintown: failed to write artist URL cache (%s)", exc)

    def _resolve_artist_url(self, artist: str) -> str | None:
        cache_key = artist.strip().lower()
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]

        artist_url = self._search_artist_url(artist)
        self._path_cache[cache_key] = artist_url
        self._save_path_cache()
        time.sleep(self.request_delay)
        return artist_url

    def _search_artist_url(self, artist: str) -> str | None:
        url = SEARCH_URL.format(query=requests.utils.quote(artist))
        html = self._get_html(url, artist, "search")
        if html is None:
            return None

        data = _parse_next_data(html)
        if data is None:
            return None

        candidates: list[tuple[str, str]] = []
        _collect_artist_candidates(data, candidates)

        best_url = None
        best_score = 0.0
        for name, candidate_url in candidates:
            score = _name_similarity(name, artist)
            if score > best_score:
                best_score = score
                best_url = candidate_url

        if best_url and best_score >= NAME_MATCH_THRESHOLD:
            if best_url.startswith("/"):
                best_url = ARTIST_URL_PREFIX + best_url
            return best_url

        log.warning("Bandsintown: no matching artist page found for %r", artist)
        return None

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def fetch_events(self, artist_to_lists: dict[str, set[str]]) -> list[Event]:
        events: list[Event] = []

        for artist, matched_lists in artist_to_lists.items():
            try:
                artist_url = self._resolve_artist_url(artist)
            except Exception as exc:
                log.warning("Bandsintown: failed to resolve a page for %r: %s", artist, exc)
                time.sleep(self.request_delay)
                continue

            if not artist_url:
                time.sleep(self.request_delay)
                continue

            try:
                html = self._get_html(artist_url, artist, "artist page")
            except Exception as exc:
                log.warning("Bandsintown: failed to fetch page for %r: %s", artist, exc)
                time.sleep(self.request_delay)
                continue

            if html is None:
                time.sleep(self.request_delay)
                continue

            try:
                page_data = _parse_next_data(html)
                if page_data is None:
                    continue

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

    def _get_html(self, url: str, artist: str, what: str) -> str | None:
        """GET a page with retries/backoff. Returns None (and logs) on 404/429/repeated errors."""
        delay = self.request_delay
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(url, headers=HEADERS, timeout=20)
            except requests.RequestException as exc:
                if attempt == self.max_retries:
                    raise
                log.warning(
                    "Bandsintown: request error fetching %s for %r (attempt %d/%d): %s — retrying",
                    what, artist, attempt, self.max_retries, exc,
                )
                time.sleep(delay)
                delay *= 2
                continue

            if resp.status_code == 429:
                if attempt == self.max_retries:
                    log.warning("Bandsintown: rate limited fetching %s for %r — giving up", what, artist)
                    return None
                log.warning(
                    "Bandsintown: rate limited (429) fetching %s for %r — backing off %.1fs",
                    what, artist, delay,
                )
                time.sleep(delay)
                delay *= 2
                continue

            if resp.status_code == 404:
                log.warning("Bandsintown: no %s found for %r (404)", what, artist)
                return None

            resp.raise_for_status()
            return resp.text

        return None


def _name_similarity(a: str, b: str) -> float:
    a, b = normalize_text(a), normalize_text(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


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


def _collect_artist_candidates(node, results: list[tuple[str, str]]) -> None:
    """Recursively find artist-like dicts: objects with 'name' and an '/a/...' url."""
    if isinstance(node, dict):
        name = node.get("name")
        url = node.get("url") or node.get("pageUrl")
        if (
            isinstance(name, str)
            and isinstance(url, str)
            and "/a/" in url
            and "datetime" not in node
            and "venue" not in node
        ):
            results.append((name, url))
        for value in node.values():
            _collect_artist_candidates(value, results)
    elif isinstance(node, list):
        for item in node:
            _collect_artist_candidates(item, results)


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
