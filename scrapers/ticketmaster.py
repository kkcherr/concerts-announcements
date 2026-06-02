"""
Ticketmaster Discovery API scraper.
Docs: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/
"""

import logging
import requests
from config import TICKETMASTER_API_KEY, WATCHLIST

log = logging.getLogger(__name__)

BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
SOURCE_NAME = "ticketmaster"


def _search_artist(artist: str) -> list[dict]:
    params = {
        "apikey": TICKETMASTER_API_KEY,
        "keyword": artist,
        "classificationName": "music",
        "size": 20,
        "sort": "date,asc",
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        log.warning("Ticketmaster request failed for %r: %s", artist, exc)
        raise

    events = []
    for item in data.get("_embedded", {}).get("events", []):
        venue_info = item.get("_embedded", {}).get("venues", [{}])[0]
        city = venue_info.get("city", {}).get("name", "")
        country = venue_info.get("country", {}).get("name", "")
        venue_name = venue_info.get("name", "")

        dates = item.get("dates", {})
        start = dates.get("start", {})
        date_str = start.get("localDate", "TBA")

        url = item.get("url", "")

        events.append(
            {
                "id": item.get("id", ""),
                "artist": artist,
                "event_name": item.get("name", artist),
                "venue": venue_name,
                "city": city,
                "country": country,
                "date": date_str,
                "url": url,
                "source": SOURCE_NAME,
            }
        )
    return events


def fetch_events() -> tuple[list[dict], str | None]:
    """
    Returns (events_list, error_message_or_None).
    """
    if not TICKETMASTER_API_KEY:
        return [], "⚠️ Ticketmaster: API key not configured."

    all_events: list[dict] = []
    errors: list[str] = []

    for artist in WATCHLIST:
        try:
            all_events.extend(_search_artist(artist))
        except Exception as exc:
            errors.append(str(exc))

    error_note = None
    if errors:
        error_note = f"⚠️ Ticketmaster: {len(errors)} artist(s) could not be fetched."

    return all_events, error_note
