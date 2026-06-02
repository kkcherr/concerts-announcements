"""
Songkick scraper — parses the artist's upcoming-events page directly
since the Songkick API is no longer open for new registrations.

Uses multiple CSS selector fallbacks so the scraper degrades gracefully
if Songkick updates their HTML structure.
"""

import hashlib
import logging
import re
import requests
from bs4 import BeautifulSoup, Tag
from config import WATCHLIST

log = logging.getLogger(__name__)

BASE_URL    = "https://www.songkick.com/search?query={query}&type=artists"
EVENTS_URL  = "https://www.songkick.com{path}/gigography?order=asc"
UPCOMING_URL = "https://www.songkick.com{path}/calendar"
SOURCE_NAME = "songkick"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}

# Candidate selectors tried in order — first match wins
ARTIST_LINK_SELECTORS = [
    "li.artist a.url",
    "li.artist a[href^='/artists/']",
    "a[href^='/artists/']",
]

EVENT_LIST_SELECTORS = [
    "li.event-listing",
    "li[class*='event']",
    "article[class*='event']",
]

DATE_SELECTORS   = ["time[datetime]", "time", "[class*='date']"]
VENUE_SELECTORS  = [
    "strong.venue-name", "strong[class*='venue']",
    "[class*='venue-name']", "[itemprop='name']",
]
LOCATION_SELECTORS = [
    "span.location", "span[class*='location']",
    "[class*='city']", "[itemprop='addressLocality']",
]
LINK_SELECTORS = [
    "a.event-link", "a[class*='event']", "a[href*='/concerts/']",
]


def _first(el: Tag, selectors: list[str]) -> Tag | None:
    for sel in selectors:
        found = el.select_one(sel)
        if found:
            return found
    return None


def _find_artist_path(artist: str) -> str | None:
    url = BASE_URL.format(query=requests.utils.quote(artist))
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        log.warning("Songkick search failed for %r: %s", artist, exc)
        raise

    soup = BeautifulSoup(resp.text, "html.parser")
    for sel in ARTIST_LINK_SELECTORS:
        for a in soup.select(sel):
            href = a.get("href", "")
            if href.startswith("/artists/"):
                return href.split("?")[0].rstrip("/")
    return None


def _fetch_events_for_path(artist: str, path: str) -> list[dict]:
    # Try gigography (historical + upcoming) first, fall back to calendar
    for url_template in (EVENTS_URL, UPCOMING_URL):
        url = url_template.format(path=path)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            break
        except Exception as exc:
            log.warning("Songkick events page failed for %r at %s: %s", artist, url, exc)
    else:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    event_items = []
    for sel in EVENT_LIST_SELECTORS:
        event_items = soup.select(sel)
        if event_items:
            break

    if not event_items:
        log.debug("No event items found on Songkick page for %r", artist)

    for li in event_items:
        date_el = _first(li, DATE_SELECTORS)
        if date_el:
            date_str = (date_el.get("datetime") or date_el.get_text(strip=True))[:10]
        else:
            date_str = "TBA"

        venue_el = _first(li, VENUE_SELECTORS)
        venue = venue_el.get_text(strip=True) if venue_el else ""

        loc_el = _first(li, LOCATION_SELECTORS)
        location = loc_el.get_text(strip=True) if loc_el else ""
        city, _, country = location.partition(", ")

        link_el = _first(li, LINK_SELECTORS)
        if link_el:
            href = link_el.get("href", "")
            event_url = ("https://www.songkick.com" + href) if href.startswith("/") else href
        else:
            event_url = ""

        uid = hashlib.md5(f"{artist}|{date_str}|{venue}".encode()).hexdigest()

        events.append(
            {
                "id":         uid,
                "artist":     artist,
                "event_name": artist,
                "venue":      venue,
                "city":       city,
                "country":    country,
                "date":       date_str,
                "url":        event_url,
                "source":     SOURCE_NAME,
            }
        )
    return events


def fetch_events() -> tuple[list[dict], str | None]:
    all_events: list[dict] = []
    errors: list[str] = []

    for artist in WATCHLIST:
        try:
            path = _find_artist_path(artist)
            if path:
                all_events.extend(_fetch_events_for_path(artist, path))
            else:
                log.debug("Songkick: no artist page found for %r", artist)
        except Exception as exc:
            errors.append(str(exc))

    error_note = None
    if errors:
        error_note = f"⚠️ Songkick: {len(errors)} artist(s) could not be fetched."

    return all_events, error_note
