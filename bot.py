"""
Telegram delivery layer.
"""

import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

log = logging.getLogger(__name__)

SEND_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_message(text: str) -> bool:
    """Send a plain-text message. Returns True on success."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.error("Telegram credentials not set — cannot send message.")
        return False

    url = SEND_URL.format(token=TELEGRAM_BOT_TOKEN)
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as exc:
        log.error("Failed to send Telegram message: %s", exc)
        return False


def send_test_message() -> bool:
    return send_message(
        "✅ <b>Concert Bot is connected!</b>\n\n"
        "This is a test message to confirm your Telegram setup works.\n"
        "Your daily digest will arrive at 9:00 AM London time."
    )


def format_digest(new_events: list[dict], errors: list[str]) -> str:
    date_header = ""
    try:
        from datetime import date
        date_header = date.today().strftime("%A, %d %B %Y")
    except Exception:
        pass

    lines = [f"<b>🎵 Concert Digest — {date_header}</b>\n"]

    if errors:
        lines.append("\n".join(errors) + "\n")

    if not new_events:
        lines.append("No new concert announcements found today. Check back tomorrow! 🎶")
        return "\n".join(lines)

    seen_artists: set[str] = set()
    for ev in new_events:
        artist = ev.get("artist", "Unknown")
        if artist not in seen_artists:
            seen_artists.add(artist)
            lines.append(f"\n{'─'*30}")

        parts = [f"\n🎤 <b>{artist}</b>"]

        event_name = ev.get("event_name", "")
        if event_name and event_name != artist:
            parts.append(f"   🎪 {event_name}")

        venue = ev.get("venue", "")
        city = ev.get("city", "")
        country = ev.get("country", "")
        location_parts = [p for p in [venue, city, country] if p]
        if location_parts:
            parts.append(f"   📍 {' · '.join(location_parts)}")

        date_val = ev.get("date", "")
        if date_val:
            parts.append(f"   📅 {date_val}")

        url = ev.get("url", "")
        if url:
            parts.append(f"   🎟️ <a href=\"{url}\">Tickets / Details</a>")

        source = ev.get("source", "")
        source_labels = {
            "ticketmaster": "Ticketmaster",
            "bandsintown": "Bandsintown",
            "songkick": "Songkick",
            "news_rss": "Google News",
        }
        parts.append(f"   📰 {source_labels.get(source, source)}")

        lines.append("\n".join(parts))

    lines.append(f"\n{'─'*30}")
    lines.append(f"\n<i>{len(new_events)} new announcement(s) today</i>")
    return "\n".join(lines)
