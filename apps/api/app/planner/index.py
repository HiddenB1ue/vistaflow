from __future__ import annotations

from dataclasses import dataclass

from app.models import StationIndex, Timetable


@dataclass(frozen=True)
class SearchIndex:
    """Station indexes used by the journey searcher."""

    departures_by_station: StationIndex
    arrivals_by_station: StationIndex

    def get(
        self,
        station: str,
        default: list[tuple[str, int]] | None = None,
    ) -> list[tuple[str, int]]:
        return self.departures_by_station.get(station, [] if default is None else default)

    def __contains__(self, station: object) -> bool:
        return station in self.departures_by_station

    def __getitem__(self, station: str) -> list[tuple[str, int]]:
        return self.departures_by_station[station]

    def __len__(self) -> int:
        return len(self.departures_by_station)


def build_station_index(timetable: Timetable) -> SearchIndex:
    """Build forward departure and reverse arrival indexes."""
    departures: StationIndex = {}
    arrivals: StationIndex = {}

    for train_no, events in timetable.items():
        for index, event in enumerate(events):
            if event.depart_abs_min is not None:
                departures.setdefault(event.station_name, []).append((train_no, index))
            if event.arrive_abs_min is not None:
                arrivals.setdefault(event.station_name, []).append((train_no, index))

    for entries in departures.values():
        entries.sort(key=lambda item: timetable[item[0]][item[1]].depart_abs_min or 0)
    for entries in arrivals.values():
        entries.sort(key=lambda item: timetable[item[0]][item[1]].arrive_abs_min or 0)

    return SearchIndex(
        departures_by_station=departures,
        arrivals_by_station=arrivals,
    )
