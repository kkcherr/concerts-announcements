"""Formats and sends the daily digest (and other messages) via the Telegram Bot API."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pycountry
import requests

from concert_bot.models import MergedEvent

log = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
MAX_MESSAGE_LENGTH = 4096

SOURCE_LABELS = {
    "ticketmaster": "Ticketmaster",
}

PRIORITY_MARKER = "🔝 PRIORITY (UK/Spain)"


class TelegramSender:
    def __init__(self, bot_token: str, chat_id: str, timezone: str = "Europe/London"):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.tz = ZoneInfo(timezone)

    # ------------------------------------------------------------------
    # Low-level sending
    # ------------------------------------------------------------------

    def send_message(self, text: str) -> bool:
        if not self.bot_token or not self.chat_id:
            log.error("Telegram credentials not set — cannot send message.")
            return False

        url = TELEGRAM_API.format(token=self.bot_token, method="sendMessage")
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if not resp.ok:
                log.warning("Telegram HTML send failed — HTTP %s: %s", resp.status_code, resp.text)
                resp.raise_for_status()
            return True
        except Exception as exc:
            log.warning("Telegram HTML send failed (%s), retrying as plain text", exc)

        plain = re.sub(r"<[^>]+>", "", text)
        payload["text"] = plain
        del payload["parse_mode"]
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if not resp.ok:
                log.error("Telegram plain-text send failed — HTTP %s: %s", resp.status_code, resp.text)
                resp.raise_for_status()
            return True
        except Exception as exc:
            log.error("Telegram plain-text send also failed: %s", exc)
            return False

    def send_messages(self, messages: list[str]) -> bool:
        ok = True
        for message in messages:
            if not self.send_message(message):
                ok = False
        return ok

    def send_test_alert(self) -> bool:
        sample = build_digest_messages(
            [_sample_event(self.tz)],
            send_when_empty=False,
            timezone=self.tz,
            header_prefix="🧪 TEST ALERT — ",
        )
        return self.send_messages(sample)

    # ------------------------------------------------------------------
    # Getting the chat id (/start command)
    # ------------------------------------------------------------------

    def run_get_chat_id(self) -> None:
        """Poll for updates and print the chat id of a /start message or channel post.

        This is a tiny helper for first-time setup:
        - For a private chat with your bot: run this, then send /start to your
          bot in Telegram, and your chat id will be printed here.
        - For a channel: add your bot to the channel as an admin (with "Post
          Messages" permission), then post anything in the channel — its chat
          id (a negative number like -100xxxxxxxxxx) will be printed here.
        """
        print("Waiting for a message...")
        print("- Private chat: open Telegram, find your bot, and send /start")
        print("- Channel: add the bot as an admin, then post anything in the channel")
        print("(Press Ctrl+C to stop)")

        url = TELEGRAM_API.format(token=self.bot_token, method="getUpdates")
        offset = None
        import json
        import time

        while True:
            params = {"timeout": 30, "allowed_updates": json.dumps(["message", "channel_post"])}
            if offset is not None:
                params["offset"] = offset
            try:
                resp = requests.get(url, params=params, timeout=35)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                log.warning("getUpdates failed: %s", exc)
                time.sleep(2)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                channel_post = update.get("channel_post")
                if channel_post is not None:
                    chat = channel_post.get("chat", {})
                    chat_id = chat.get("id")
                    if chat_id is not None:
                        print(f"\nYour Telegram channel's chat id is: {chat_id}")
                        print("Add this to your .env file as TELEGRAM_CHAT_ID")
                        return

                message = update.get("message", {})
                text = message.get("text", "")
                chat = message.get("chat", {})
                chat_id = chat.get("id")
                if text.strip().startswith("/start") and chat_id is not None:
                    print(f"\nYour Telegram chat id is: {chat_id}")
                    print("Add this to your .env file as TELEGRAM_CHAT_ID")
                    return


# ----------------------------------------------------------------------
# Digest formatting
# ----------------------------------------------------------------------


def build_digest_messages(
    merged_events: list[MergedEvent],
    send_when_empty: bool,
    timezone: ZoneInfo,
    header_prefix: str = "",
) -> list[str]:
    """Build one or more Telegram messages (HTML) for the daily digest.

    Returns an empty list if there is nothing new and send_when_empty is False.
    """
    date_header = datetime.now(timezone).strftime("%A, %d %B %Y")
    title = f"{header_prefix}🎵 <b>Concert Digest — {date_header}</b>"

    if not merged_events:
        if not send_when_empty:
            return []
        return [f"{title}\n\nNo new concert announcements today. 🎶"]

    entry_blocks = [_format_entry(event, timezone) for event in merged_events]

    messages: list[str] = []
    current = title
    for block in entry_blocks:
        candidate = current + "\n\n" + block
        if len(candidate) > MAX_MESSAGE_LENGTH:
            messages.append(current)
            current = block
        else:
            current = candidate
    messages.append(current)

    if len(messages) > 1:
        messages = [f"{m}\n\n<i>(part {i + 1}/{len(messages)})</i>" for i, m in enumerate(messages)]

    return messages


def _strip_artist_prefix(event_name: str | None, artist: str) -> str:
    """Return the concert/tour name with the artist prefix removed, or '' if none."""
    if not event_name or event_name.strip().lower() == artist.strip().lower():
        return ""
    name = event_name.strip()
    prefix = artist.strip()
    if name.lower().startswith(prefix.lower()):
        remainder = name[len(prefix):].lstrip(" :-|–—")
        if remainder:
            return remainder
    return name


def _format_entry(event: MergedEvent, timezone: ZoneInfo) -> str:
    lines = []

    if event.priority:
        lines.append(f"⭐ <b>{PRIORITY_MARKER}</b>")

    concert_name = _strip_artist_prefix(event.event_name, event.artist)
    if concert_name:
        lines.append(f"🎤 <b>{_escape(event.artist)} : {_escape(concert_name)}</b>")
    else:
        lines.append(f"🎤 <b>{_escape(event.artist)}</b>")

    venue_city = [p for p in [event.venue, event.city] if p]
    if venue_city:
        lines.append(f"📍 {_escape(' · '.join(venue_city))}")
    if event.country:
        country_obj = pycountry.countries.get(alpha_2=event.country)
        country_name = country_obj.name if country_obj else event.country
        lines.append(f"🌍 {_escape(country_name)}")

    date_str = event.event_date.strftime("%a %d %b %Y") if event.event_date else "Date TBA"
    lines.append(f"📅 {date_str}")

    if event.onsale_datetime or event.presales:
        lines.append("")

    if event.onsale_datetime:
        local_onsale = event.onsale_datetime.astimezone(timezone)
        lines.append(f"🛒 General onsale: {local_onsale.strftime('%a %d %b %Y, %H:%M %Z')}")

    if event.presales:
        presale_lines = ["<b>🎟️ Presales:</b>"]
        for presale in event.presales:
            start = presale.start.astimezone(timezone).strftime("%a %d %b, %H:%M %Z") if presale.start else "TBA"
            end = presale.end.astimezone(timezone).strftime("%a %d %b, %H:%M %Z") if presale.end else "TBA"
            presale_lines.append(f"   • <b>{_escape(presale.name)}</b>: {start} → {end}")
        lines.append("\n".join(presale_lines))

    if event.onsale_datetime or event.presales:
        lines.append("")

    for source_name, url in event.urls:
        label = SOURCE_LABELS.get(source_name, source_name)
        lines.append(f'🎟️ <a href="{url}">{label} link</a>')

    if event.matched_lists:
        lists_str = ", ".join(sorted(event.matched_lists))
        lines.append(f"📋 List: {lists_str}")

    sources_str = ", ".join(SOURCE_LABELS.get(s, s) for s in event.sources)
    lines.append(f"📰 Source: {sources_str}")

    return "\n".join(lines)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _sample_event(timezone: ZoneInfo) -> MergedEvent:
    from datetime import date, timedelta

    from concert_bot.models import Presale

    now = datetime.now(timezone)
    return MergedEvent(
        artist="Sample Artist",
        event_name="Sample Artist: The World Tour",
        venue="The O2 Arena",
        city="London",
        country="GB",
        event_date=date.today() + timedelta(days=120),
        event_time="19:30",
        onsale_datetime=now + timedelta(days=3),
        presales=[
            Presale(name="O2 Priority", start=now + timedelta(days=1), end=now + timedelta(days=2)),
        ],
        sources=["ticketmaster"],
        urls=[("ticketmaster", "https://www.ticketmaster.co.uk/")],
        matched_lists={"must_see"},
        priority=True,
    )
