"""
Telegram delivery layer.
"""

import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

log = logging.getLogger(__name__)

SEND_URL = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MSG_LEN = 4096  # Telegram hard limit


MAX_EVENTS = 30  # cap per digest so the message always fits in one Telegram message


def send_message(text: str) -> bool:
    """Send a single message. Falls back to plain text if HTML is rejected."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.error("Telegram credentials not set — cannot send message.")
        return False

    url = SEND_URL.format(token=TELEGRAM_BOT_TOKEN)

    # Try with HTML formatting first
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
        log.warning("HTML send failed (%s), retrying as plain text", exc)

    # Strip HTML tags and retry as plain text
    import re
    plain = re.sub(r"<[^>]+>", "", text)
    payload["text"] = plain
    del payload["parse_mode"]
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as exc:
        log.error("Plain text send also failed: %s", exc)
        return False


def send_test_message() -> bool:
    return send_message(
        "✅ <b>Concert Bot is connected!</b>\n\n"
        "This is a test message to confirm your Telegram setup works.\n"
        "Your daily digest will arrive at 9:00 AM London time."
    )


SOURCE_LABELS = {
    "ticketmaster": "Ticketmaster",
    "bandsintown":  "Bandsintown",
    "songkick":     "Songkick",
    "news_rss":     "Google News",
}


def _format_event(ev: dict) -> str:
    artist = ev.get("artist", "Unknown Artist")
    parts = [f"🎤 <b>{artist}</b>"]

    event_name = ev.get("event_name", "")
    if event_name and event_name.strip().lower() != artist.strip().lower():
        parts.append(f"   🎪 {event_name}")

    venue   = ev.get("venue", "")
    city    = ev.get("city", "")
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
    parts.append(f"   📰 {SOURCE_LABELS.get(source, source or 'Unknown')}")

    return "\n".join(parts)


def format_digest(new_events: list[dict], errors: list[str]) -> str:
    from datetime import date
    date_header = date.today().strftime("%A, %d %B %Y")

    total = len(new_events)
    shown = new_events[:MAX_EVENTS]
    overflow = total - len(shown)

    lines = [f"<b>🎵 Concert Digest — {date_header}</b>"]

    if errors:
        lines.append("")
        lines.extend(errors)

    if not shown:
        lines.append("\nNo new concert announcements found today. Check back tomorrow! 🎶")
        return "\n".join(lines)

    divider = "─" * 30
    for ev in shown:
        lines.append(f"\n{divider}")
        lines.append(_format_event(ev))

    lines.append(f"\n{divider}")
    if overflow:
        lines.append(f"\n<i>Showing {len(shown)} of {total} new announcements today</i>")
    else:
        lines.append(f"\n<i>{total} new announcement(s) today</i>")
    return "\n".join(lines)


def send_digest(new_events: list[dict], errors: list[str]) -> bool:
    digest = format_digest(new_events, errors)
    return send_message(digest)
