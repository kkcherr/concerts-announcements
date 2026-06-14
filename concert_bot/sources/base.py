"""Abstract base class every concert data source must implement."""

from __future__ import annotations

from abc import ABC, abstractmethod

from concert_bot.models import Event


class Source(ABC):
    """Common interface for a concert data source.

    A source is given a mapping of artist name -> set of tracked list names
    (e.g. {"Adele": {"must_see"}}) and must return normalized Event objects,
    each tagged with the list(s) the artist matched.
    """

    name: str

    @abstractmethod
    def fetch_events(self, artist_to_lists: dict[str, set[str]]) -> list[Event]:
        """Fetch new/upcoming events for every tracked artist.

        Implementations must never raise — catch and log errors per-artist
        so that one failure doesn't stop the whole run, and return whatever
        events were successfully gathered.
        """
        raise NotImplementedError
