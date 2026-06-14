import json
from datetime import date
from pathlib import Path

from concert_bot.sources.bandsintown import (
    _extract_events,
    _parse_event,
    _slugify,
    _validate_artist_page,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    with open(FIXTURES / name, "r", encoding="utf-8") as f:
        return json.load(f)


def test_slugify():
    assert _slugify("Sample Artist") == "sample-artist"
    assert _slugify("Florence + The Machine") == "florence-the-machine"
    assert _slugify("AC/DC") == "ac-dc"


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
