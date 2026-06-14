"""Combines events from every source, deduplicates, and applies priority sorting."""

from __future__ import annotations

import logging

from concert_bot.models import Event, MergedEvent, normalize_text, venue_similarity

log = logging.getLogger(__name__)

# How similar two venue names need to be (0.0-1.0) to be considered the same venue.
VENUE_SIMILARITY_THRESHOLD = 0.6


def aggregate(events: list[Event], priority_countries: list[str]) -> list[MergedEvent]:
    """Group, dedupe and merge raw events into MergedEvent objects.

    Events are grouped first by (normalized artist, event date, normalized city),
    then within each group, clustered by fuzzy venue-name similarity so the same
    show reported by two sources collapses into one entry.
    """
    priority_set = {c.upper() for c in priority_countries}

    groups: dict[tuple[str, str, str], list[Event]] = {}
    for event in events:
        key = (
            normalize_text(event.artist),
            event.event_date.isoformat() if event.event_date else "unknown-date",
            normalize_text(event.city),
        )
        groups.setdefault(key, []).append(event)

    merged: list[MergedEvent] = []
    for group_key, group_events in groups.items():
        for cluster in _cluster_by_venue(group_events):
            merged.append(_merge_cluster(cluster, group_key, priority_set))

    # Sort: priority entries first, then by event date.
    merged.sort(key=_sort_key)
    return merged


def _cluster_by_venue(events: list[Event]) -> list[list[Event]]:
    """Group events that share an (already-matching) artist/date/city by venue similarity."""
    clusters: list[list[Event]] = []
    for event in events:
        placed = False
        for cluster in clusters:
            if any(venue_similarity(event.venue, other.venue) >= VENUE_SIMILARITY_THRESHOLD for other in cluster):
                cluster.append(event)
                placed = True
                break
            # Events with no venue info at all are assumed to be the same show.
            if not event.venue and not cluster[0].venue:
                cluster.append(event)
                placed = True
                break
        if not placed:
            clusters.append([event])
    return clusters


def _merge_cluster(
    cluster: list[Event], group_key: tuple[str, str, str], priority_countries: set[str]
) -> MergedEvent:
    # Prefer the entry with the most complete info as the "primary" record.
    primary = max(cluster, key=lambda e: (bool(e.venue), bool(e.country), len(e.presales)))

    sources = []
    urls: list[tuple[str, str]] = []
    presales = []
    matched_lists: set[str] = set()
    country = primary.country
    onsale_datetime = primary.onsale_datetime

    for event in cluster:
        if event.source not in sources:
            sources.append(event.source)
        if event.url:
            urls.append((event.source, event.url))
        presales.extend(event.presales)
        matched_lists |= event.matched_lists
        if not country and event.country:
            country = event.country
        if onsale_datetime is None and event.onsale_datetime is not None:
            onsale_datetime = event.onsale_datetime

    # De-dupe identical presale entries (same name/start/end) across sources.
    unique_presales = []
    seen_presales = set()
    for presale in presales:
        key = (presale.name, presale.start, presale.end)
        if key not in seen_presales:
            seen_presales.add(key)
            unique_presales.append(presale)

    is_priority = country.upper() in priority_countries

    artist_norm, date_str, city_norm = group_key

    merged_event = MergedEvent(
        artist=primary.artist,
        event_name=primary.event_name,
        venue=primary.venue,
        city=primary.city,
        country=country,
        event_date=primary.event_date,
        event_time=primary.event_time,
        onsale_datetime=onsale_datetime,
        presales=unique_presales,
        sources=sources,
        urls=urls,
        matched_lists=matched_lists,
        priority=is_priority,
    )
    return merged_event


def _sort_key(event: MergedEvent):
    # Priority entries first (False sorts before True, so negate).
    priority_rank = 0 if event.priority else 1
    date_rank = event.event_date.isoformat() if event.event_date else "9999-99-99"
    return (priority_rank, date_rank, normalize_text(event.artist))
