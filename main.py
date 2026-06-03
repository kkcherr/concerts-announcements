"""
Concert Announcement Bot — entry point.
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("concert_bot")


def _setup() -> bool:
    from setup_wizard import check_env_or_setup
    ok = check_env_or_setup()
    if not ok:
        return False

    # Reload config after wizard may have written .env
    import importlib
    import config
    importlib.reload(config)
    return True


def run_digest(force: bool = False) -> None:
    """Fetch all sources, deduplicate, format, and send the Telegram digest.
    If force=True, skip deduplication and send everything found.
    """
    import os
    from db import init_db, filter_new
    from bot import send_digest
    from scrapers import ticketmaster, bandsintown, songkick, news_rss

    # Wipe the database when --force is used so all events are treated as new
    if force:
        db_path = os.environ.get("DB_PATH", "concerts.db")
        if os.path.exists(db_path):
            os.remove(db_path)
            log.info("--force: cleared seen-events database")

    init_db()

    all_events: list[dict] = []
    errors: list[str] = []

    sources = [
        ("Ticketmaster", "ticketmaster", ticketmaster.fetch_events),
        ("Bandsintown",  "bandsintown",  bandsintown.fetch_events),
        ("Songkick",     "songkick",     songkick.fetch_events),
        ("Google News",  "news_rss",     news_rss.fetch_events),
    ]

    for name, source_key, fetcher in sources:
        try:
            events, error_note = fetcher()
            log.info("%s returned %d event(s)", name, len(events))
            new = filter_new(source_key, events)
            log.info("%s has %d new event(s) after dedup", name, len(new))
            all_events.extend(new)
            if error_note:
                errors.append(error_note)
        except Exception as exc:
            msg = f"⚠️ {name} couldn't be reached today."
            log.error("%s failed: %s", name, exc)
            errors.append(msg)

    log.info("Sending digest (%d new events)...", len(all_events))
    send_digest(all_events, errors)


def start_scheduler() -> None:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from config import DIGEST_HOUR, DIGEST_MINUTE, TIMEZONE

    scheduler = BlockingScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        run_digest,
        trigger="cron",
        hour=DIGEST_HOUR,
        minute=DIGEST_MINUTE,
        id="daily_digest",
    )
    log.info(
        "Scheduler started — digest will run daily at %02d:%02d %s",
        DIGEST_HOUR,
        DIGEST_MINUTE,
        TIMEZONE,
    )
    print(
        f"\n✅ Bot is running! Daily digest scheduled for "
        f"{DIGEST_HOUR:02d}:{DIGEST_MINUTE:02d} ({TIMEZONE}).\n"
        "Press Ctrl+C to stop.\n"
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")


if __name__ == "__main__":
    if not _setup():
        sys.exit(1)

    if "--run-now" in sys.argv:
        force = "--force" in sys.argv
        log.info("Running digest immediately (force=%s)...", force)
        run_digest(force=force)
        sys.exit(0)

    # Send a Telegram test message if this is first run
    if "--test" in sys.argv:
        from bot import send_test_message
        ok = send_test_message()
        print("✅ Test message sent!" if ok else "❌ Test message failed — check your credentials.")
        sys.exit(0 if ok else 1)

    start_scheduler()
