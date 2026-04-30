from __future__ import annotations

from datetime import date, time
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import NAMESPACE_DNS, uuid5

import pytest

from app.exceptions import BusinessError, NotFoundError
from app.journey_search_sessions.schemas import (
    CachedRouteCandidate,
    CachedTrainSegment,
    SearchSessionCreateRequest,
    SearchSessionViewRequest,
)
from app.journey_search_sessions.service import JourneySearchSessionService
from app.journeys.schemas import JourneyResult, JourneySearchResponse, JourneySegment
from app.route_plan_cache.repository import (
    RoutePlanAvailableFacets,
    RoutePlanQueryFilters,
    RoutePlanViewQuery,
    RoutePlanViewResult,
)


def _build_search_response() -> JourneySearchResponse:
    return JourneySearchResponse(
        journeys=[
            JourneyResult(
                id="direct-1",
                is_direct=True,
                total_duration_minutes=120,
                departure_date="2026-04-15",
                departure_time="08:00",
                arrival_date="2026-04-15",
                arrival_time="10:00",
                segments=[
                    JourneySegment(
                        train_no="240000G1010A",
                        train_code="G1",
                        from_station="Beijing South",
                        to_station="Shanghai Hongqiao",
                        departure_date="2026-04-15",
                        departure_time="08:00",
                        arrival_date="2026-04-15",
                        arrival_time="10:00",
                        duration_minutes=120,
                        stops_count=2,
                    )
                ],
            ),
            JourneyResult(
                id="transfer-1",
                is_direct=False,
                total_duration_minutes=180,
                departure_date="2026-04-15",
                departure_time="07:30",
                arrival_date="2026-04-16",
                arrival_time="10:30",
                segments=[
                    JourneySegment(
                        train_no="240000G1010A",
                        train_code="G1",
                        from_station="Beijing South",
                        to_station="Jinan West",
                        departure_date="2026-04-15",
                        departure_time="07:30",
                        arrival_date="2026-04-15",
                        arrival_time="08:30",
                        duration_minutes=60,
                        stops_count=1,
                    ),
                    JourneySegment(
                        train_no="240000D1100B",
                        train_code="D11",
                        from_station="Jinan West",
                        to_station="Shanghai Hongqiao",
                        departure_date="2026-04-16",
                        departure_time="09:00",
                        arrival_date="2026-04-16",
                        arrival_time="10:30",
                        duration_minutes=90,
                        stops_count=2,
                    ),
                ],
            ),
        ],
        total=2,
        date="2026-04-15",
    )


@pytest.fixture
def service() -> JourneySearchSessionService:
    journey_service = MagicMock()
    journey_service.search = AsyncMock(return_value=_build_search_response())

    station_repo = MagicMock()
    station_repo.get_geo_by_names = AsyncMock(
        return_value={
            "Beijing South": (116.38, 39.87),
            "Shanghai Hongqiao": (121.31, 31.19),
            "Jinan West": (116.89, 36.67),
        }
    )

    ticket_service = MagicMock()
    ticket_service.enrich_routes_for_view = AsyncMock(
        side_effect=lambda *, run_date, routes: routes
    )
    ticket_service.prefetch_all_prices = AsyncMock(return_value={})

    route_plan_repo = MagicMock()
    plans: dict[int, dict[str, object]] = {}
    candidates_by_plan_id: dict[str, list[CachedRouteCandidate]] = {}

    async def find_ready_plan(
        *,
        from_station: str,
        to_station: str,
        search_date: date,
        transfer_count: int,
    ) -> dict[str, object] | None:
        plan = plans.get(transfer_count)
        if plan and plan["status"] == 1:
            return plan
        return None

    async def replace_plan(
        *,
        from_station: str,
        to_station: str,
        search_date: date,
        transfer_count: int,
        expires_at: Any,
        candidates: list[CachedRouteCandidate],
    ) -> dict[str, object]:
        plan_id = str(uuid5(NAMESPACE_DNS, f"plan-{transfer_count}"))
        plan = {
            "plan_id": plan_id,
            "from_station": from_station,
            "to_station": to_station,
            "search_date": search_date,
            "transfer_count": transfer_count,
            "status": 1,
            "total_candidates": len(candidates),
            "expires_at": expires_at,
        }
        plans[transfer_count] = plan
        candidates_by_plan_id[plan_id] = [
            candidate
            for candidate in candidates
            if candidate.transferCount == transfer_count
        ]
        return plan

    async def get_plans_by_ids(plan_ids: list[str]) -> list[dict[str, object]]:
        wanted = set(plan_ids)
        return [plan for plan in plans.values() if plan["plan_id"] in wanted]

    async def list_candidates(plan_ids: list[str]) -> list[CachedRouteCandidate]:
        return [
            candidate
            for plan_id in plan_ids
            for candidate in candidates_by_plan_id.get(plan_id, [])
        ]

    async def count_candidates(
        plan_ids: list[str],
        filters: RoutePlanQueryFilters,
    ) -> int:
        return len(_filter_candidates(await list_candidates(plan_ids), filters))

    async def query_view(plan_ids: list[str], query: RoutePlanViewQuery) -> RoutePlanViewResult:
        candidates = _filter_candidates(await list_candidates(plan_ids), query.filters)
        facets = RoutePlanAvailableFacets(
            transfer_counts=sorted({candidate.transferCount for candidate in candidates}),
            train_types=sorted(
                {train_type for candidate in candidates for train_type in candidate.trainTypes}
            ),
        )
        if query.transfer_counts:
            candidates = [
                candidate
                for candidate in candidates
                if candidate.transferCount in query.transfer_counts
            ]
        if query.exclude_direct_train_codes_in_transfer_routes:
            direct_codes = {
                code
                for candidate in candidates
                if candidate.isDirect
                for code in candidate.trainCodes
            }
            candidates = [
                candidate
                for candidate in candidates
                if candidate.isDirect
                or all(code not in direct_codes for code in candidate.trainCodes)
            ]
        if query.display_train_types:
            candidates = [
                candidate
                for candidate in candidates
                if set(candidate.trainTypes).issubset(query.display_train_types)
            ]
        if query.sort_by == "departure":
            candidates.sort(
                key=lambda candidate: (
                    candidate.transferCount,
                    candidate.departureTime,
                    candidate.durationMinutes,
                )
            )
        else:
            candidates.sort(
                key=lambda candidate: (
                    candidate.transferCount,
                    candidate.durationMinutes,
                    candidate.departureTime,
                )
            )
        total = len(candidates)
        start = (query.page - 1) * query.page_size
        return RoutePlanViewResult(
            candidates=candidates[start : start + query.page_size],
            total=total,
            facets=facets,
        )

    async def delete_plans(plan_ids: list[str]) -> int:
        count = 0
        for transfer_count, plan in list(plans.items()):
            if plan["plan_id"] in plan_ids:
                del plans[transfer_count]
                candidates_by_plan_id.pop(str(plan["plan_id"]), None)
                count += 1
        return count

    route_plan_repo.find_ready_plan = AsyncMock(side_effect=find_ready_plan)
    route_plan_repo.replace_plan = AsyncMock(side_effect=replace_plan)
    route_plan_repo.get_plans_by_ids = AsyncMock(side_effect=get_plans_by_ids)
    route_plan_repo.count_candidates = AsyncMock(side_effect=count_candidates)
    route_plan_repo.query_view = AsyncMock(side_effect=query_view)
    route_plan_repo.delete_plans = AsyncMock(side_effect=delete_plans)
    route_plan_repo.plans = plans

    return JourneySearchSessionService(
        ttl_seconds=900,
        journey_service=journey_service,
        station_repo=station_repo,
        ticket_service=ticket_service,
        route_plan_repo=route_plan_repo,
    )


def _filter_candidates(
    candidates: list[CachedRouteCandidate],
    filters: RoutePlanQueryFilters,
) -> list[CachedRouteCandidate]:
    result: list[CachedRouteCandidate] = []
    for candidate in candidates:
        train_codes = {code.strip().upper() for code in candidate.trainCodes}
        train_segments = [
            segment
            for segment in candidate.segs
            if isinstance(segment, CachedTrainSegment)
        ]
        train_nos = {segment.trainNo.strip().upper() for segment in train_segments}
        transfer_stations = {
            segment.destination.name for segment in train_segments[:-1]
        }

        if filters.allowed_train_types and not set(candidate.trainTypes).issubset(
            filters.allowed_train_types
        ):
            continue
        if filters.excluded_train_types and not set(candidate.trainTypes).isdisjoint(
            filters.excluded_train_types
        ):
            continue
        if filters.allowed_trains and train_codes.isdisjoint(
            filters.allowed_trains
        ) and train_nos.isdisjoint(filters.allowed_trains):
            continue
        if filters.excluded_trains and (
            not train_codes.isdisjoint(filters.excluded_trains)
            or not train_nos.isdisjoint(filters.excluded_trains)
        ):
            continue
        if filters.departure_time_start_min is not None or (
            filters.departure_time_end_min is not None
        ):
            departure_min = _time_to_minutes(candidate.departureTime)
            start = filters.departure_time_start_min
            end = filters.departure_time_end_min
            if start is not None and end is not None and start > end:
                if not (departure_min >= start or departure_min <= end):
                    continue
            elif (
                (start is not None and departure_min < start)
                or (end is not None and departure_min > end)
            ):
                continue
        if filters.arrival_deadline_abs_min is not None:
            arrival_min = _time_to_minutes(candidate.arrivalTime)
            if filters.arrival_deadline_abs_min >= 1440:
                arrival_min += _date_offset_days(candidate.arrivalDate) * 1440
            if arrival_min > filters.arrival_deadline_abs_min:
                continue
        waits: list[int] = []
        for previous, current in zip(train_segments, train_segments[1:], strict=False):
            previous_arrival = _time_to_minutes(previous.arrivalTime)
            current_departure = _time_to_minutes(current.departureTime)
            if current.departureDate > previous.arrivalDate:
                current_departure += 1440
            waits.append(current_departure - previous_arrival)
        if any(wait < filters.min_transfer_minutes for wait in waits):
            continue
        if (
            filters.max_transfer_minutes is not None
            and any(wait > filters.max_transfer_minutes for wait in waits)
        ):
            continue
        if (
            filters.allowed_transfer_stations
            and candidate.transferCount > 0
            and transfer_stations.isdisjoint(filters.allowed_transfer_stations)
        ):
            continue
        if filters.excluded_transfer_stations and not transfer_stations.isdisjoint(
            filters.excluded_transfer_stations
        ):
            continue
        result.append(candidate)
    return result


def _time_to_minutes(value: str) -> int:
    hours, minutes = value.split(":", maxsplit=1)
    return int(hours) * 60 + int(minutes)


def _date_offset_days(value: str) -> int:
    return (date.fromisoformat(value) - date(2026, 4, 15)).days


@pytest.mark.asyncio
async def test_create_session_generates_route_plan_cache_and_returns_first_view(
    service: JourneySearchSessionService,
) -> None:
    response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=True,
        )
    )

    assert response.searchSummary.totalCandidates == 2
    assert response.viewResult.total == 2
    assert len(response.viewResult.items) == 2
    assert response.viewResult.items[0].departureDate == "2026-04-15"
    assert response.viewResult.items[1].arrivalDate == "2026-04-16"
    first_transfer_segment = response.viewResult.items[1].segs[0]
    assert first_transfer_segment.departureDate == "2026-04-15"
    assert response.viewResult.availableFacets.transferCounts == [0, 1]
    assert response.viewResult.availableFacets.trainTypes == ["D", "G"]
    journey_service = cast(Any, service._journey_service)
    assert journey_service.search.await_args_list[0].args[0].display_limit == 0
    route_plan_repo = cast(Any, service._route_plan_repo)
    assert route_plan_repo.replace_plan.await_count == 2


@pytest.mark.asyncio
async def test_reuses_ready_route_plan_without_research(
    service: JourneySearchSessionService,
) -> None:
    first_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=True,
        )
    )

    second_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=True,
        )
    )

    assert first_response.searchSummary.totalCandidates == 2
    assert second_response.searchSummary.totalCandidates == 2
    journey_service = cast(Any, service._journey_service)
    assert journey_service.search.await_count == 2


@pytest.mark.asyncio
async def test_unavailable_route_plan_is_regenerated(
    service: JourneySearchSessionService,
) -> None:
    first_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=False,
        )
    )

    repo = cast(Any, service._route_plan_repo)
    repo.plans[1]["status"] = 0

    second_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=False,
        )
    )

    assert first_response.searchId != ""
    assert second_response.searchSummary.totalCandidates == 1
    journey_service = cast(Any, service._journey_service)
    assert journey_service.search.await_count == 2


@pytest.mark.asyncio
async def test_no_timetable_error_is_not_cached_as_empty_route_plan(
    service: JourneySearchSessionService,
) -> None:
    journey_service = cast(Any, service._journey_service)
    journey_service.search.side_effect = BusinessError(
        "暂无该日期的列车时刻数据: 2026-04-15",
        http_status=404,
    )

    with pytest.raises(BusinessError):
        await service.create_session(
            SearchSessionCreateRequest(
                from_station="Beijing South",
                to_station="Shanghai Hongqiao",
                date=date(2026, 4, 15),
                transfer_count=1,
                include_fewer_transfers=False,
            )
        )

    route_plan_repo = cast(Any, service._route_plan_repo)
    route_plan_repo.replace_plan.assert_not_called()


@pytest.mark.asyncio
async def test_view_switch_does_not_trigger_research(
    service: JourneySearchSessionService,
) -> None:
    create_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=True,
        )
    )

    departure_view = await service.get_view(
        create_response.searchId,
        SearchSessionViewRequest(sort_by="departure", include_tickets=False),
    )

    assert departure_view.items[0].id == "direct-1"
    journey_service = cast(Any, service._journey_service)
    assert journey_service.search.await_count == 2


@pytest.mark.asyncio
async def test_transfer_count_filter_works_against_route_plan_candidates(
    service: JourneySearchSessionService,
) -> None:
    create_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=True,
        )
    )

    filtered_view = await service.get_view(
        create_response.searchId,
        SearchSessionViewRequest(transfer_counts=[0]),
    )

    assert filtered_view.total == 1
    assert [item.id for item in filtered_view.items] == ["direct-1"]
    assert filtered_view.appliedView.transferCounts == [0]


@pytest.mark.asyncio
async def test_create_filters_do_not_create_distinct_route_plan(
    service: JourneySearchSessionService,
) -> None:
    await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=True,
        )
    )

    filtered_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=True,
            allowed_train_types=["G"],
        )
    )

    assert filtered_response.searchSummary.totalCandidates == 1
    assert [item.id for item in filtered_response.viewResult.items] == ["direct-1"]
    journey_service = cast(Any, service._journey_service)
    assert journey_service.search.await_count == 2


@pytest.mark.asyncio
async def test_create_filters_are_applied_to_reused_route_plan_candidates(
    service: JourneySearchSessionService,
) -> None:
    await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=True,
        )
    )

    filtered_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=True,
            departure_time_start=time(7, 0),
            departure_time_end=time(7, 45),
            arrival_deadline=time(11, 0),
            min_transfer_minutes=120,
            allowed_transfer_stations=["Jinan West"],
            excluded_trains=["G9"],
        )
    )

    assert filtered_response.searchSummary.totalCandidates == 1
    assert [item.id for item in filtered_response.viewResult.items] == ["transfer-1"]
    journey_service = cast(Any, service._journey_service)
    assert journey_service.search.await_count == 2


@pytest.mark.asyncio
async def test_zero_max_transfer_minutes_means_unlimited_like_planner(
    service: JourneySearchSessionService,
) -> None:
    await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=True,
        )
    )

    filtered_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=True,
            allowed_transfer_stations=["Jinan West"],
            departure_time_start=time(7, 0),
            departure_time_end=time(7, 45),
            max_transfer_minutes=0,
        )
    )

    assert filtered_response.searchSummary.totalCandidates == 1
    assert [item.id for item in filtered_response.viewResult.items] == ["transfer-1"]
    journey_service = cast(Any, service._journey_service)
    assert journey_service.search.await_count == 2


@pytest.mark.asyncio
async def test_exclude_direct_train_codes_filters_transfer_routes(
    service: JourneySearchSessionService,
) -> None:
    create_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=True,
        )
    )

    filtered_view = await service.get_view(
        create_response.searchId,
        SearchSessionViewRequest(
            exclude_direct_train_codes_in_transfer_routes=True,
        ),
    )

    assert filtered_view.total == 1
    assert [item.id for item in filtered_view.items] == ["direct-1"]


@pytest.mark.asyncio
async def test_missing_search_context_raises_not_found(
    service: JourneySearchSessionService,
) -> None:
    with pytest.raises(NotFoundError):
        await service.get_view("missing-session", SearchSessionViewRequest())


@pytest.mark.asyncio
async def test_invalid_search_context_plan_id_raises_not_found(
    service: JourneySearchSessionService,
) -> None:
    invalid_context = "eyJwbGFuSWRzIjpbIm5vdC1hLXV1aWQiXX0"

    with pytest.raises(NotFoundError):
        await service.get_view(invalid_context, SearchSessionViewRequest())


@pytest.mark.asyncio
async def test_delete_search_context_does_not_delete_shared_route_plans(
    service: JourneySearchSessionService,
) -> None:
    create_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
            transfer_count=1,
            include_fewer_transfers=True,
        )
    )

    delete_response = await service.delete_session(create_response.searchId)

    assert delete_response.deleted is True
    route_plan_repo = cast(Any, service._route_plan_repo)
    route_plan_repo.delete_plans.assert_not_called()
