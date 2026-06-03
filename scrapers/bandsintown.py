"""
Bandsintown API scraper (v3, free personal-use tier).
Docs: https://app.swaggerhub.com/apis/Bandsintown/PublicAPI/3.0.0
"""

import logging
import requests
from config import BANDSINTOWN_APP_ID, WATCHLIST

log = logging.getLogger(__name__)

BASE_URL = "https://rest.bandsintown.com/artists/{artist}/events"
SOURCE_NAME = "bandsintown"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def _search_artist(artist: str) -> list[dict]:
    url = BASE_URL.format(artist=requests.utils.quote(artist))
    params = {"app_id": BANDSINTOWN_APP_ID, "date": "upcoming"}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        log.warning("Bandsintown request failed for %r: %s", artist, exc)
        raise

    if not isinstance(data, list):
        return []

    events = []
    for item in data:
        venue = item.get("venue", {})
        events.append(
            {
                "id": str(item.get("id", "")),
                "artist": artist,
                "event_name": item.get("title") or artist,
                "venue": venue.get("name", ""),
                "city": venue.get("city", ""),
                "country": venue.get("country", ""),
                "date": item.get("datetime", "")[:10],
                "url": item.get("url", ""),
                "source": SOURCE_NAME,
            }
        )
    return events


def fetch_events() -> tuple[list[dict], str | None]:
    if not BANDSINTOWN_APP_ID:
        return [], "⚠️ Bandsintown: app ID not configured."

    all_events: list[dict] = []
    errors: list[str] = []

    for artist in WATCHLIST:
        try:
            all_events.extend(_search_artist(artist))
        except Exception as exc:
            errors.append(str(exc))

    error_note = None
    if errors:
        error_note = f"⚠️ Bandsintown: {len(errors)} artist(s) could not be fetched."

    return all_events, error_note
