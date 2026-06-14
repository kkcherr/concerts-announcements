"""Concert Digest Bot — entry point.

Usage:
    python main.py                 Start the daily scheduler (runs forever)
    python main.py --run-now       Run one digest cycle immediately and exit
    python main.py --dry-run       Like --run-now, but print the digest instead of sending it
    python main.py --test-alert    Send one sample digest message to Telegram
    python main.py --get-chat-id   Wait for a /start message and print your chat id
    python main.py --source NAME   Only run a single source (ticketmaster|bandsintown)
"""

from __future__ import annotations

import argparse
import logging
import sys

from concert_bot.aggregator import aggregate
from concert_bot.config import Config, all_tracked_artists, artist_to_lists, load_config
from concert_bot.models import MergedEvent
from concert_bot.sources.bandsintown import BandsintownSource
from concert_bot.sources.base import Source
from concert_bot.sources.ticketmaster import TicketmasterSource
from concert_bot.state import StateStore
from concert_bot.telegram_sender import TelegramSender, build_digest_messages

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("concert_bot")


def build_sources(config: Config) -> list[Source]:
    sources: list[Source] = []
    if config.sources.get("ticketmaster", True):
        sources.append(TicketmasterSource(config))
    if config.sources.get("bandsintown", True):
        sources.append(BandsintownSource(config))
    return sources


def run_digest(config: Config, dry_run: bool = False, only_source: str | None = None) -> list[MergedEvent]:
    """Fetch all sources, dedupe, send (or print) the digest. Returns the new events sent."""
    artist_lists_map = artist_to_lists(config.artist_lists)
    total_artists = len(all_tracked_artists(config.artist_lists))
    log.info("Starting digest run — tracking %d artist(s) across %d list(s)",
             total_artists, len(config.artist_lists))

    sources = build_sources(config)
    if only_source:
        sources = [s for s in sources if s.name == only_source]
        if not sources:
            log.error("Unknown or disabled source: %r", only_source)
            return []

    all_events = []
    for source in sources:
        try:
            events = source.fetch_events(artist_lists_map)
            all_events.extend(events)
        except Exception:
            log.exception("Source %r failed unexpectedly — continuing with other sources", source.name)

    merged = aggregate(all_events, config.priority_countries)
    log.info("Aggregated %d raw event(s) into %d unique event(s)", len(all_events), len(merged))

    state = StateStore(config.paths.state_db)
    canonical_keys = [m.canonical_key for m in merged]
    new_keys = state.filter_new(canonical_keys)
    new_events = [m for m in merged if m.canonical_key in new_keys]

    for event in new_events:
        log.info(
            "NEW: %s — %s, %s, %s on %s%s",
            event.artist,
            event.venue or "venue TBA",
            event.city or "city TBA",
            event.country or "?",
            event.event_date.isoformat() if event.event_date else "date TBA",
            " [PRIORITY]" if event.priority else "",
        )

    sender = TelegramSender(config.telegram_bot_token, config.telegram_chat_id, config.timezone)
    messages = build_digest_messages(new_events, config.send_when_empty, sender.tz)

    if dry_run:
        if not messages:
            print("\n(Nothing new today — no message would be sent, send_when_empty is off.)\n")
        for i, message in enumerate(messages, 1):
            print(f"\n----- Message {i}/{len(messages)} -----")
            print(message)
        return new_events

    if messages:
        ok = sender.send_messages(messages)
        if not ok:
            log.error("Failed to send digest to Telegram.")
    else:
        log.info("Nothing new today — send_when_empty is off, no message sent.")

    if new_events:
        state.mark_seen([e.canonical_key for e in new_events])

    log.info("Digest run complete — %d new event(s)", len(new_events))
    return new_events


def main() -> None:
    parser = argparse.ArgumentParser(description="Concert Digest Bot")
    parser.add_argument("--run-now", action="store_true", help="Run one digest cycle immediately and exit")
    parser.add_argument("--dry-run", action="store_true", help="Print the digest instead of sending it")
    parser.add_argument("--test-alert", action="store_true", help="Send one sample digest message to Telegram")
    parser.add_argument("--get-chat-id", action="store_true", help="Wait for a /start message and print your chat id")
    parser.add_argument("--source", choices=["ticketmaster", "bandsintown"], help="Only run this source")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config) if args.config else load_config()

    if args.get_chat_id:
        sender = TelegramSender(config.telegram_bot_token, config.telegram_chat_id or "0", config.timezone)
        sender.run_get_chat_id()
        return

    if args.test_alert:
        sender = TelegramSender(config.telegram_bot_token, config.telegram_chat_id, config.timezone)
        ok = sender.send_test_alert()
        print("Test alert sent! Check your Telegram." if ok else "Failed to send test alert — check your .env credentials.")
        sys.exit(0 if ok else 1)

    if args.dry_run:
        run_digest(config, dry_run=True, only_source=args.source)
        return

    if args.run_now:
        run_digest(config, dry_run=False, only_source=args.source)
        return

    from concert_bot.scheduler import start_scheduler

    start_scheduler(lambda: run_digest(config), config.daily_run_time, config.timezone)


if __name__ == "__main__":
    main()
