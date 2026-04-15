from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.exceptions import NotFoundError
from app.journey_search_sessions.schemas import (
    SearchSessionCreateRequest,
    SearchSessionViewRequest,
)
from app.journey_search_sessions.service import JourneySearchSessionService
from app.journeys.schemas import JourneyResult, JourneySearchResponse, JourneySegment, SeatSchema


def _build_search_response() -> JourneySearchResponse:
    return JourneySearchResponse(
        journeys=[
            JourneyResult(
                id="direct-1",
                is_direct=True,
                total_duration_minutes=120,
                departure_time="08:00",
                arrival_time="10:00",
                min_price=320.0,
                segments=[
                    JourneySegment(
                        train_code="G1",
                        from_station="Beijing South",
                        to_station="Shanghai Hongqiao",
                        departure_time="08:00",
                        arrival_time="10:00",
                        duration_minutes=120,
                        stops_count=2,
                        seats=[
                            SeatSchema(
                                seat_type="ze",
                                status="available",
                                price=320.0,
                                available=True,
                            )
                        ],
                    )
                ],
            ),
            JourneyResult(
                id="transfer-1",
                is_direct=False,
                total_duration_minutes=180,
                departure_time="07:30",
                arrival_time="10:30",
                min_price=280.0,
                segments=[
                    JourneySegment(
                        train_code="G1",
                        from_station="Beijing South",
                        to_station="Jinan West",
                        departure_time="07:30",
                        arrival_time="08:30",
                        duration_minutes=60,
                        stops_count=1,
                        seats=[
                            SeatSchema(
                                seat_type="zy",
                                status="available",
                                price=180.0,
                                available=True,
                            )
                        ],
                    ),
                    JourneySegment(
                        train_code="D11",
                        from_station="Jinan West",
                        to_station="Shanghai Hongqiao",
                        departure_time="09:00",
                        arrival_time="10:30",
                        duration_minutes=90,
                        stops_count=2,
                        seats=[
                            SeatSchema(
                                seat_type="ze",
                                status="available",
                                price=100.0,
                                available=True,
                            )
                        ],
                    ),
                ],
            ),
        ],
        total=2,
        date="2026-04-15",
    )


@pytest.fixture
def service(fake_redis) -> JourneySearchSessionService:
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

    return JourneySearchSessionService(
        redis_client=fake_redis,
        ttl_seconds=900,
        journey_service=journey_service,
        station_repo=station_repo,
    )


@pytest.mark.asyncio
async def test_create_session_caches_candidates_and_returns_first_view(
    service: JourneySearchSessionService,
) -> None:
    response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
        )
    )

    assert response.searchSummary.totalCandidates == 2
    assert response.viewResult.total == 2
    assert len(response.viewResult.items) == 2
    assert response.viewResult.availableFacets.transferCounts == [0, 1]
    assert response.viewResult.availableFacets.trainTypes == ["D", "G"]


@pytest.mark.asyncio
async def test_view_switch_does_not_trigger_research(
    service: JourneySearchSessionService,
) -> None:
    create_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
        )
    )

    price_view = await service.get_view(
        create_response.searchId,
        SearchSessionViewRequest(sort_by="price"),
    )

    assert price_view.items[0].id == "transfer-1"
    service._journey_service.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_transfer_count_filter_works_against_cached_candidates(
    service: JourneySearchSessionService,
) -> None:
    create_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
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
async def test_exclude_direct_train_codes_filters_transfer_routes(
    service: JourneySearchSessionService,
) -> None:
    create_response = await service.create_session(
        SearchSessionCreateRequest(
            from_station="Beijing South",
            to_station="Shanghai Hongqiao",
            date=date(2026, 4, 15),
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
async def test_missing_search_session_raises_not_found(
    service: JourneySearchSessionService,
) -> None:
    with pytest.raises(NotFoundError):
        await service.get_view("missing-session", SearchSessionViewRequest())
