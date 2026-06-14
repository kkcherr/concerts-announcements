from datetime import date, datetime, timezone

from concert_bot.aggregator import aggregate
from concert_bot.models import Event, Presale


def _ticketmaster_event(**overrides) -> Event:
    base = dict(
        artist="Sample Artist",
        event_name="Sample Artist: The World Tour",
        venue="The O2 Arena",
        city="London",
        country="GB",
        event_date=date(2026, 9, 12),
        event_time="19:30",
        onsale_datetime=datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc),
        presales=[Presale(name="O2 Priority", start=datetime(2026, 6, 17, 9, 0, tzinfo=timezone.utc), end=None)],
        source="ticketmaster",
        url="https://www.ticketmaster.co.uk/sample-artist/123",
        matched_lists={"must_see"},
    )
    base.update(overrides)
    return Event(**base)


def _other_source_event(**overrides) -> Event:
    base = dict(
        artist="Sample Artist",
        event_name="Sample Artist at The O2",
        venue="O2 Arena",  # slightly different spelling than Ticketmaster's "The O2 Arena"
        city="London",
        country="GB",
        event_date=date(2026, 9, 12),
        event_time="18:30",
        onsale_datetime=None,
        presales=[],
        source="other_source",
        url="https://example.com/e/event-1",
        matched_lists={"must_see"},
    )
    base.update(overrides)
    return Event(**base)


def test_dedupes_same_show_across_sources():
    events = [_ticketmaster_event(), _other_source_event()]
    merged = aggregate(events, priority_countries=["GB", "ES"])

    assert len(merged) == 1
    entry = merged[0]
    assert set(entry.sources) == {"ticketmaster", "other_source"}
    assert len(entry.urls) == 2
    assert entry.priority is True
    # Ticketmaster's presale data should be kept even though the dupe came from the other source.
    assert len(entry.presales) == 1
    assert entry.presales[0].name == "O2 Priority"
    # matched_lists merged from both sources
    assert entry.matched_lists == {"must_see"}


def test_does_not_merge_different_venues_same_city_and_date():
    events = [
        _ticketmaster_event(),
        _ticketmaster_event(venue="Wembley Stadium", url="https://www.ticketmaster.co.uk/sample-artist/456"),
    ]
    merged = aggregate(events, priority_countries=["GB", "ES"])
    assert len(merged) == 2


def test_priority_countries_sorted_first():
    uk_event = _ticketmaster_event()
    us_event = _ticketmaster_event(
        venue="Madison Square Garden",
        city="New York",
        country="US",
        event_date=date(2026, 8, 1),
        url="https://www.ticketmaster.com/sample-artist/789",
        presales=[],
        onsale_datetime=None,
    )

    merged = aggregate([us_event, uk_event], priority_countries=["GB", "ES"])

    assert merged[0].country == "GB"
    assert merged[0].priority is True
    assert merged[1].country == "US"
    assert merged[1].priority is False


def test_canonical_key_stable_for_same_show():
    events = [_ticketmaster_event(), _other_source_event()]
    merged = aggregate(events, priority_countries=["GB", "ES"])
    key = merged[0].canonical_key
    assert "sample artist" in key
    assert "2026-09-12" in key
    assert "london" in key
