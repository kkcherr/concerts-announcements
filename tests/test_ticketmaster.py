import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from concert_bot.sources.ticketmaster import TicketmasterSource, _parse_date, _parse_datetime

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    with open(FIXTURES / name, "r", encoding="utf-8") as f:
        return json.load(f)


class FakeConfig:
    ticketmaster_api_key = "fake-key"

    class ticketmaster:
        events_page_size = 50
        request_delay_seconds = 0.0
        announcement_lookback_hours = 26

    class paths:
        ticketmaster_attraction_cache = "/tmp/does-not-exist-tm-cache.json"


def _source(tmp_path) -> TicketmasterSource:
    config = FakeConfig()
    config.paths.ticketmaster_attraction_cache = str(tmp_path / "attractions.json")
    return TicketmasterSource(config)


def test_parse_datetime_handles_utc_zulu():
    dt = _parse_datetime("2026-06-17T09:00:00Z")
    assert dt == datetime(2026, 6, 17, 9, 0, tzinfo=timezone.utc)


def test_parse_date():
    assert _parse_date("2026-09-12") == date(2026, 9, 12)
    assert _parse_date(None) is None


def test_parse_event_extracts_presales(tmp_path):
    source = _source(tmp_path)
    data = _load_fixture("ticketmaster_events.json")
    raw_event = data["_embedded"]["events"][0]

    event = source._parse_event(raw_event, "Sample Artist", {"must_see"})

    assert event.artist == "Sample Artist"
    assert event.venue == "The O2 Arena"
    assert event.city == "London"
    assert event.country == "GB"
    assert event.event_date == date(2026, 9, 12)
    assert event.event_time == "19:30"
    assert event.onsale_datetime == datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc)
    assert event.matched_lists == {"must_see"}

    assert len(event.presales) == 2
    names = {p.name for p in event.presales}
    assert names == {"O2 Priority", "Artist Fan Club Presale"}

    fan_club = next(p for p in event.presales if p.name == "Artist Fan Club Presale")
    assert fan_club.start == datetime(2026, 6, 16, 9, 0, tzinfo=timezone.utc)
    assert fan_club.end == datetime(2026, 6, 17, 8, 59, tzinfo=timezone.utc)


def test_parse_event_with_no_presales(tmp_path):
    source = _source(tmp_path)
    data = _load_fixture("ticketmaster_events.json")
    raw_event = data["_embedded"]["events"][1]

    event = source._parse_event(raw_event, "Sample Artist", {"blockbusters"})

    assert event.presales == []
    assert event.country == "US"
    assert event.city == "New York"


def test_fetch_events_filters_by_recent_announcement(tmp_path, monkeypatch):
    source = _source(tmp_path)

    captured_params = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"_embedded": {"events": []}, "page": {"totalPages": 1}}

    def fake_get(url, params=None, timeout=None):
        captured_params.update(params)
        return FakeResponse()

    monkeypatch.setattr("concert_bot.sources.ticketmaster.requests.get", fake_get)

    source._fetch_events_for_attraction("K8vZ9171Ki0")

    assert "publicVisibilityStartDateTime" in captured_params
    cutoff = datetime.fromisoformat(captured_params["publicVisibilityStartDateTime"].replace("Z", "+00:00"))
    expected = datetime.now(timezone.utc) - timedelta(hours=26)
    assert abs((cutoff - expected).total_seconds()) < 5


def test_attraction_cache_round_trip(tmp_path, monkeypatch):
    source = _source(tmp_path)

    calls = []

    def fake_lookup(self, artist):
        calls.append(artist)
        return "K8vZ9171Ki0"

    monkeypatch.setattr(TicketmasterSource, "_lookup_attraction_id", fake_lookup)

    first = source._resolve_attraction_id("Sample Artist")
    second = source._resolve_attraction_id("Sample Artist")

    assert first == "K8vZ9171Ki0"
    assert second == "K8vZ9171Ki0"
    # The lookup should only have hit the network once — second call used the cache.
    assert calls == ["Sample Artist"]

    # A fresh source instance reading the same cache file should not need to look up again.
    source2 = TicketmasterSource(FakeConfig())
    source2.cache_path = source.cache_path
    source2._cache = source2._load_cache()
    monkeypatch.setattr(TicketmasterSource, "_lookup_attraction_id", fake_lookup)
    assert source2._resolve_attraction_id("Sample Artist") == "K8vZ9171Ki0"
    assert calls == ["Sample Artist"]
