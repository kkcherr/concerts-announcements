"""Configuration loading.

Non-secret settings (artist lists, schedule, toggles) live in config.yaml.
Secrets (API keys, Telegram credentials) come from environment variables
(optionally loaded from a local .env file) and are never hardcoded.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


@dataclass
class Paths:
    state_db: str = "data/state.db"
    ticketmaster_attraction_cache: str = "data/ticketmaster_attractions.json"


@dataclass
class TicketmasterConfig:
    events_page_size: int = 50
    request_delay_seconds: float = 0.25
    announcement_lookback_hours: int = 26


@dataclass
class BandsintownConfig:
    request_delay_seconds: float = 2.0
    max_retries: int = 3


@dataclass
class Config:
    artist_lists: dict[str, list[str]]
    priority_countries: list[str]
    daily_run_time: str
    timezone: str
    send_when_empty: bool
    sources: dict[str, bool]
    paths: Paths
    ticketmaster: TicketmasterConfig
    bandsintown: BandsintownConfig

    # Secrets, read from the environment.
    ticketmaster_api_key: str = field(default="")
    bandsintown_app_id: str = field(default="")
    telegram_bot_token: str = field(default="")
    telegram_chat_id: str = field(default="")


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    artist_lists_raw = raw.get("artist_lists", {})
    artist_lists = {
        list_name: list(spec.get("artists", []))
        for list_name, spec in artist_lists_raw.items()
    }

    paths_raw = raw.get("paths", {})
    paths = Paths(
        state_db=paths_raw.get("state_db", Paths.state_db),
        ticketmaster_attraction_cache=paths_raw.get(
            "ticketmaster_attraction_cache", Paths.ticketmaster_attraction_cache
        ),
    )

    tm_raw = raw.get("ticketmaster", {})
    ticketmaster = TicketmasterConfig(
        events_page_size=int(tm_raw.get("events_page_size", TicketmasterConfig.events_page_size)),
        request_delay_seconds=float(
            tm_raw.get("request_delay_seconds", TicketmasterConfig.request_delay_seconds)
        ),
        announcement_lookback_hours=int(
            tm_raw.get("announcement_lookback_hours", TicketmasterConfig.announcement_lookback_hours)
        ),
    )

    bit_raw = raw.get("bandsintown", {})
    bandsintown = BandsintownConfig(
        request_delay_seconds=float(
            bit_raw.get("request_delay_seconds", BandsintownConfig.request_delay_seconds)
        ),
        max_retries=int(bit_raw.get("max_retries", BandsintownConfig.max_retries)),
    )

    return Config(
        artist_lists=artist_lists,
        priority_countries=[c.upper() for c in raw.get("priority_countries", ["GB", "ES"])],
        daily_run_time=str(raw.get("daily_run_time", "19:00")),
        timezone=raw.get("timezone", "Europe/London"),
        send_when_empty=bool(raw.get("send_when_empty", False)),
        sources=raw.get("sources", {"ticketmaster": True, "bandsintown": True}),
        paths=paths,
        ticketmaster=ticketmaster,
        bandsintown=bandsintown,
        ticketmaster_api_key=os.getenv("TICKETMASTER_API_KEY", ""),
        bandsintown_app_id=os.getenv("BANDSINTOWN_APP_ID", ""),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
    )


def artist_to_lists(artist_lists: dict[str, list[str]]) -> dict[str, set[str]]:
    """Invert artist_lists into a mapping of artist name -> set of list names."""
    mapping: dict[str, set[str]] = {}
    for list_name, artists in artist_lists.items():
        for artist in artists:
            mapping.setdefault(artist, set()).add(list_name)
    return mapping


def all_tracked_artists(artist_lists: dict[str, list[str]]) -> list[str]:
    """Return a de-duplicated list of every tracked artist across all lists."""
    seen: dict[str, None] = {}
    for artists in artist_lists.values():
        for artist in artists:
            seen.setdefault(artist, None)
    return list(seen.keys())
