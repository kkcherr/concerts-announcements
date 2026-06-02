"""
Google News RSS scraper.
Searches for "[artist] tour 2025 2026 announced" headlines.
Also checks for major non-watchlist artist tour announcements.
"""

import hashlib
import logging
import xml.etree.ElementTree as ET
import requests
from config import WATCHLIST

log = logging.getLogger(__name__)

SOURCE_NAME = "news_rss"

RSS_URL = (
    "https://news.google.com/rss/search"
    "?q={query}&hl=en-US&gl=US&ceid=US:en"
)

MAJOR_TOUR_QUERY = (
    '"tour announced" OR "new tour" OR "world tour" 2025 2026 concert'
)


def _fetch_rss(query: str) -> list[dict]:
    url = RSS_URL.format(query=requests.utils.quote(query))
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        log.warning("News RSS request failed for query %r: %s", query, exc)
        raise

    root = ET.fromstring(resp.content)
    items = []
    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        pub_date = item.findtext("pubDate") or ""

        uid = hashlib.md5(link.encode()).hexdigest()
        items.append(
            {
                "id": uid,
                "artist": "",
                "event_name": title,
                "venue": "",
                "city": "",
                "country": "",
                "date": pub_date[:16],
                "url": link,
                "source": SOURCE_NAME,
            }
        )
    return items


def _artist_query(artist: str) -> str:
    return f'"{artist}" tour 2025 OR 2026 announced'


def fetch_events() -> tuple[list[dict], str | None]:
    all_events: list[dict] = []
    errors: list[str] = []

    for artist in WATCHLIST:
        try:
            items = _fetch_rss(_artist_query(artist))
            for item in items:
                item["artist"] = artist
            all_events.extend(items)
        except Exception as exc:
            errors.append(str(exc))

    try:
        major = _fetch_rss(MAJOR_TOUR_QUERY)
        for item in major:
            item["artist"] = "📢 Major artist"
        all_events.extend(major)
    except Exception as exc:
        errors.append(str(exc))

    error_note = None
    if errors:
        error_note = f"⚠️ Google News RSS: {len(errors)} query/queries failed."

    return all_events, error_note
