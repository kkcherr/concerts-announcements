import json
from datetime import date, datetime, timezone
from pathlib import Path

from concert_bot.sources.bandsintown import (
    BandsintownSource,
    _country_code,
    _parse_datetime,
    _parse_event,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    with open(FIXTURES / name, "r", encoding="utf-8") as f:
        return json.load(f)


class FakeConfig:
    bandsintown_app_id = "fake-app-id"

    class bandsintown:
        request_delay_seconds = 0.0
        max_retries = 3


def _source() -> BandsintownSource:
    return BandsintownSource(FakeConfig())


def test_parse_datetime_handles_naive_value():
    dt = _parse_datetime("2026-06-20T09:00:00")
    assert dt == datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc)


def test_parse_datetime_handles_none():
    assert _parse_datetime(None) is None


def test_country_code_normalizes_names():
    assert _country_code("United Kingdom") == "GB"
    assert _country_code("Spain") == "ES"
    assert _country_code("gb") == "GB"
    assert _country_code("") == ""


def test_parse_event_with_onsale_and_offers():
    data = _load_fixture("bandsintown_events.json")
    event = _parse_event(data[0], "Sample Artist", {"must_see"})

    assert event.artist == "Sample Artist"
    assert event.venue == "The O2 Arena"
    assert event.city == "London"
    assert event.country == "GB"
    assert event.event_date == date(2026, 9, 12)
    assert event.event_time == "18:30"
    assert event.onsale_datetime == datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc)
    assert event.presales == []
    assert event.url == "https://www.bandsintown.com/e/event-1"
    assert event.matched_lists == {"must_see"}


def test_parse_event_without_onsale_or_offers():
    data = _load_fixture("bandsintown_events.json")
    event = _parse_event(data[1], "Sample Artist", {"legends"})

    assert event.country == "ES"
    assert event.city == "Madrid"
    assert event.onsale_datetime is None
    assert event.url == "https://www.bandsintown.com/e/event-2"


def test_fetch_artist_events_returns_none_on_404(monkeypatch):
    source = _source()

    class FakeResponse:
        status_code = 404

    monkeypatch.setattr(
        "concert_bot.sources.bandsintown.requests.get",
        lambda url, params=None, timeout=None: FakeResponse(),
    )

    assert source._fetch_artist_events("Unknown Artist") is None


def test_fetch_artist_events_returns_list(monkeypatch):
    source = _source()
    data = _load_fixture("bandsintown_events.json")

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return data

    monkeypatch.setattr(
        "concert_bot.sources.bandsintown.requests.get",
        lambda url, params=None, timeout=None: FakeResponse(),
    )

    events = source._fetch_artist_events("Sample Artist")
    assert events == data


def test_fetch_events_skips_when_no_app_id():
    class NoAppIdConfig(FakeConfig):
        bandsintown_app_id = ""

    source = BandsintownSource(NoAppIdConfig())
    assert source.fetch_events({"Sample Artist": {"must_see"}}) == []
