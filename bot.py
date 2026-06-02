"""
Telegram delivery layer.
"""

import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

log = logging.getLogger(__name__)

SEND_URL = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MSG_LEN = 4096  # Telegram hard limit


def send_message(text: str) -> bool:
    """Send a message, splitting automatically if it exceeds Telegram's limit."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.error("Telegram credentials not set — cannot send message.")
        return False

    chunks = _split_message(text)
    ok = True
    for chunk in chunks:
        ok = _send_chunk(chunk) and ok
    return ok


def _send_chunk(text: str) -> bool:
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


def _split_message(text: str) -> list[str]:
    """Split on newlines so we never cut in the middle of a line."""
    if len(text) <= MAX_MSG_LEN:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in text.split("\n"):
        line_len = len(line) + 1  # +1 for the newline
        if current_len + line_len > MAX_MSG_LEN and current:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len

    if current:
        chunks.append("\n".join(current))

    return chunks


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

    lines = [f"<b>🎵 Concert Digest — {date_header}</b>"]

    if errors:
        lines.append("")
        lines.extend(errors)

    if not new_events:
        lines.append("\nNo new concert announcements found today. Check back tomorrow! 🎶")
        return "\n".join(lines)

    divider = "─" * 30
    for ev in new_events:
        lines.append(f"\n{divider}")
        lines.append(_format_event(ev))

    lines.append(f"\n{divider}")
    lines.append(f"\n<i>{len(new_events)} new announcement(s) today</i>")
    return "\n".join(lines)


def send_digest(new_events: list[dict], errors: list[str]) -> bool:
    digest = format_digest(new_events, errors)
    return send_message(digest)
