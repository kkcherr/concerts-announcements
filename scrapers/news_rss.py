"""
Google News RSS scraper.
Searches for "[artist] concert/tour announced" headlines.
Also checks for major non-watchlist artist tour announcements.
"""

import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import date
import requests
from config import WATCHLIST

log = logging.getLogger(__name__)

SOURCE_NAME = "news_rss"

RSS_URL = (
    "https://news.google.com/rss/search"
    "?q={query}&hl=en-US&gl=US&ceid=US:en"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


def _current_years() -> str:
    """Return a query fragment like '2026 OR 2027' based on today's year."""
    this_year = date.today().year
    return f"{this_year} OR {this_year + 1}"


def _major_tour_query() -> str:
    years = _current_years()
    return f'"tour announced" OR "new tour" OR "world tour" {years} concert'


def _fetch_rss(query: str) -> list[dict]:
    url = RSS_URL.format(query=requests.utils.quote(query))
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        log.warning("News RSS request failed for query %r: %s", query, exc)
        raise

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        log.warning("Failed to parse RSS XML: %s", exc)
        return []

    items = []
    for item in root.findall(".//item"):
        title    = item.findtext("title") or ""
        link     = item.findtext("link") or ""
        pub_date = item.findtext("pubDate") or ""

        # Strip the " - Source Name" suffix Google appends to titles
        if " - " in title:
            title = title.rsplit(" - ", 1)[0].strip()

        uid = hashlib.md5(link.encode()).hexdigest()
        items.append(
            {
                "id":         uid,
                "artist":     "",
                "event_name": title,
                "venue":      "",
                "city":       "",
                "country":    "",
                "date":       pub_date[:16],
                "url":        link,
                "source":     SOURCE_NAME,
            }
        )
    return items


def _artist_query(artist: str) -> str:
    years = _current_years()
    return f'"{artist}" (concert OR tour OR show OR gig OR announced) {years}'


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
        major = _fetch_rss(_major_tour_query())
        for item in major:
            item["artist"] = "📢 Major artist"
        all_events.extend(major)
    except Exception as exc:
        errors.append(str(exc))

    error_note = None
    if errors:
        error_note = f"⚠️ Google News RSS: {len(errors)} query/queries failed."

    return all_events, error_note
