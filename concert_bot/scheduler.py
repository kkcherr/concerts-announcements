"""Daily scheduling via APScheduler."""

from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

log = logging.getLogger(__name__)


def start_scheduler(run_digest_fn, daily_run_time: str, timezone: str) -> None:
    """Run run_digest_fn() once a day at daily_run_time (HH:MM) in the given timezone."""
    hour_str, minute_str = daily_run_time.split(":")
    hour, minute = int(hour_str), int(minute_str)

    scheduler = BlockingScheduler(timezone=timezone)
    scheduler.add_job(
        run_digest_fn,
        trigger="cron",
        hour=hour,
        minute=minute,
        id="daily_digest",
    )

    print(
        f"\nConcert digest bot is running.\n"
        f"The daily digest is scheduled for {hour:02d}:{minute:02d} ({timezone}).\n"
        f"Press Ctrl+C to stop.\n"
    )
    log.info("Scheduler started — daily digest at %02d:%02d %s", hour, minute, timezone)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")
