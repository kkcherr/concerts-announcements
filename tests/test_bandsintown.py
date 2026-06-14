import json
from datetime import date
from pathlib import Path

from concert_bot.sources.bandsintown import (
    BandsintownSource,
    _collect_artist_candidates,
    _extract_events,
    _name_similarity,
    _parse_event,
    _validate_artist_page,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    with open(FIXTURES / name, "r", encoding="utf-8") as f:
        return json.load(f)


class FakeConfig:
    class bandsintown:
        request_delay_seconds = 0.0
        max_retries = 3

    class paths:
        bandsintown_artist_path_cache = "/tmp/does-not-exist-bit-cache.json"


def _source(tmp_path) -> BandsintownSource:
    config = FakeConfig()
    config.paths.bandsintown_artist_path_cache = str(tmp_path / "artist_paths.json")
    return BandsintownSource(config)


def test_name_similarity():
    assert _name_similarity("Sample Artist", "Sample Artist") == 1.0
    assert _name_similarity("Sample Artist", "Totally Different") < 0.5


def test_collect_artist_candidates_finds_artists_and_skips_events():
    data = _load_fixture("bandsintown_search.json")
    candidates = []
    _collect_artist_candidates(data, candidates)

    names = {name for name, _ in candidates}
    assert "Sample Artist" in names
    assert "Sample Artist Tribute Band" in names
    # The event-like dict (has "datetime"/"venue") should not be collected.
    assert "Sample Artist at The O2 Arena" not in names


def test_search_artist_url_picks_best_match(tmp_path, monkeypatch):
    source = _source(tmp_path)

    html = (
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(_load_fixture("bandsintown_search.json"))
        + "</script>"
    )

    class FakeResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        "concert_bot.sources.bandsintown.requests.get",
        lambda url, headers=None, timeout=None: FakeResponse(),
    )

    url = source._search_artist_url("Sample Artist")

    assert url == "https://www.bandsintown.com/a/12345-sample-artist"


def test_resolve_artist_url_caches_result(tmp_path, monkeypatch):
    source = _source(tmp_path)

    calls = []

    def fake_search(self, artist):
        calls.append(artist)
        return "https://www.bandsintown.com/a/12345-sample-artist"

    monkeypatch.setattr(BandsintownSource, "_search_artist_url", fake_search)

    first = source._resolve_artist_url("Sample Artist")
    second = source._resolve_artist_url("Sample Artist")

    assert first == "https://www.bandsintown.com/a/12345-sample-artist"
    assert second == first
    assert calls == ["Sample Artist"]

    # A fresh source instance reading the same cache file should not need to search again.
    source2 = BandsintownSource(FakeConfig())
    source2.path_cache_path = source.path_cache_path
    source2._path_cache = source2._load_path_cache()
    monkeypatch.setattr(BandsintownSource, "_search_artist_url", fake_search)
    assert source2._resolve_artist_url("Sample Artist") == first
    assert calls == ["Sample Artist"]


def test_validate_artist_page_accepts_matching_artist():
    data = _load_fixture("bandsintown_next_data.json")
    assert _validate_artist_page(data, "Sample Artist") is True
    assert _validate_artist_page(data, "Some Other Artist") is False


def test_extract_events_finds_all_events():
    data = _load_fixture("bandsintown_next_data.json")
    events = _extract_events(data)
    assert len(events) == 2
    titles = {e["title"] for e in events}
    assert titles == {"Sample Artist at The O2 Arena", "Sample Artist at Wizink Center"}


def test_parse_event_normalizes_country_and_date():
    data = _load_fixture("bandsintown_next_data.json")
    raw_events = _extract_events(data)
    london_event = next(e for e in raw_events if "O2" in e["title"])

    event = _parse_event(london_event, "Sample Artist", {"must_see"})

    assert event.artist == "Sample Artist"
    assert event.venue == "The O2 Arena"
    assert event.city == "London"
    assert event.country == "GB"
    assert event.event_date == date(2026, 9, 12)
    assert event.event_time == "18:30"
    assert event.presales == []
    assert event.onsale_datetime is None
    assert event.url == "https://www.bandsintown.com/e/event-1"
    assert event.matched_lists == {"must_see"}


def test_parse_event_spain_country_code():
    data = _load_fixture("bandsintown_next_data.json")
    raw_events = _extract_events(data)
    madrid_event = next(e for e in raw_events if "Wizink" in e["title"])

    event = _parse_event(madrid_event, "Sample Artist", {"legends"})

    assert event.country == "ES"
    assert event.city == "Madrid"


def test_extract_events_on_malformed_data_returns_empty():
    assert _extract_events({"foo": "bar"}) == []
    assert _extract_events({}) == []
