"""
Songkick scraper — parses the artist's upcoming-events page directly
since the Songkick API is no longer open for new registrations.
"""

import hashlib
import logging
import re
import requests
from bs4 import BeautifulSoup
from config import WATCHLIST

log = logging.getLogger(__name__)

BASE_URL = "https://www.songkick.com/search?query={query}&type=artists"
EVENTS_URL = "https://www.songkick.com{path}/gigography?order=asc"
SOURCE_NAME = "songkick"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _find_artist_path(artist: str) -> str | None:
    url = BASE_URL.format(query=requests.utils.quote(artist))
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        log.warning("Songkick search failed for %r: %s", artist, exc)
        raise

    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.select("li.artist a.url"):
        href = a.get("href", "")
        if href.startswith("/artists/"):
            return href.rstrip("/")
    return None


def _fetch_events_for_path(artist: str, path: str) -> list[dict]:
    url = EVENTS_URL.format(path=path)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        log.warning("Songkick events page failed for %r: %s", artist, exc)
        raise

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    for li in soup.select("li.event-listing"):
        date_el = li.select_one("time")
        date_str = date_el.get("datetime", "")[:10] if date_el else "TBA"

        venue_el = li.select_one("p.venue-details strong.venue-name")
        venue = venue_el.get_text(strip=True) if venue_el else ""

        loc_el = li.select_one("p.venue-details span.location")
        location = loc_el.get_text(strip=True) if loc_el else ""
        city, _, country = location.partition(", ")

        link_el = li.select_one("a.event-link")
        event_url = "https://www.songkick.com" + link_el.get("href", "") if link_el else ""

        uid = hashlib.md5(f"{artist}|{date_str}|{venue}".encode()).hexdigest()

        events.append(
            {
                "id": uid,
                "artist": artist,
                "event_name": artist,
                "venue": venue,
                "city": city,
                "country": country,
                "date": date_str,
                "url": event_url,
                "source": SOURCE_NAME,
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
        except Exception as exc:
            errors.append(str(exc))

    error_note = None
    if errors:
        error_note = f"⚠️ Songkick: {len(errors)} artist(s) could not be fetched."

    return all_events, error_note
