from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.journey_search_sessions.dependencies import get_journey_search_session_service
from app.journey_search_sessions.schemas import (
    SearchSessionAvailableFacetsResponse,
    SearchSessionCreateResponse,
    SearchSessionDeleteResponse,
    SearchSessionSummaryResponse,
    SearchSessionViewResponse,
    SearchSessionViewResultResponse,
    SearchSummaryResponse,
)
from app.main import app


@pytest.fixture
def mock_search_session_service() -> MagicMock:
    service = MagicMock()
    service.create_session = AsyncMock(
        return_value=SearchSessionCreateResponse(
            searchId="session-1",
            expiresAt=datetime(2026, 4, 15, 10, 0, tzinfo=UTC),
            searchSummary=SearchSummaryResponse(
                fromStation="Beijing South",
                toStation="Shanghai Hongqiao",
                date="2026-04-15",
                totalCandidates=2,
            ),
            viewResult=SearchSessionViewResultResponse.build(
                items=[],
                total=0,
                view=SearchSessionViewResponse(
                    sortBy="duration",
                    excludeDirectTrainCodesInTransferRoutes=False,
                    displayTrainTypes=[],
                    transferCounts=[],
                    page=1,
                    pageSize=20,
                    includeTickets=True,
                ),
                facets=SearchSessionAvailableFacetsResponse(
                    transferCounts=[0, 1],
                    trainTypes=["D", "G"],
                ),
            ),
        )
    )
    service.get_summary = AsyncMock(
        return_value=SearchSessionSummaryResponse(
            searchId="session-1",
            expiresAt=datetime(2026, 4, 15, 10, 0, tzinfo=UTC),
            searchSummary=SearchSummaryResponse(
                fromStation="Beijing South",
                toStation="Shanghai Hongqiao",
                date="2026-04-15",
                totalCandidates=2,
            ),
        )
    )
    service.get_view = AsyncMock(
        return_value=SearchSessionViewResultResponse.build(
            items=[],
            total=0,
            view=SearchSessionViewResponse(
                sortBy="price",
                excludeDirectTrainCodesInTransferRoutes=False,
                displayTrainTypes=[],
                transferCounts=[0],
                page=1,
                pageSize=20,
                includeTickets=True,
            ),
            facets=SearchSessionAvailableFacetsResponse(
                transferCounts=[0, 1],
                trainTypes=["D", "G"],
            ),
        )
    )
    service.delete_session = AsyncMock(
        return_value=SearchSessionDeleteResponse(deleted=True)
    )
    return service


@pytest.fixture
def client_with_session_service(
    mock_search_session_service: MagicMock,
) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_journey_search_session_service] = (
        lambda: mock_search_session_service
    )
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_create_search_session(client_with_session_service: TestClient) -> None:
    response = client_with_session_service.post(
        "/api/v1/journey-search-sessions",
        json={
            "from_station": "Beijing South",
            "to_station": "Shanghai Hongqiao",
            "date": "2026-04-15",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["searchId"] == "session-1"
    assert response.json()["data"]["viewResult"]["availableFacets"]["transferCounts"] == [
        0,
        1,
    ]


def test_get_search_session_summary(client_with_session_service: TestClient) -> None:
    response = client_with_session_service.get("/api/v1/journey-search-sessions/session-1")

    assert response.status_code == 200
    assert response.json()["data"]["searchSummary"]["totalCandidates"] == 2


def test_get_search_session_view(client_with_session_service: TestClient) -> None:
    response = client_with_session_service.post(
        "/api/v1/journey-search-sessions/session-1/view",
        json={
            "sort_by": "price",
            "transfer_counts": [0],
            "page": 1,
            "page_size": 20,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["appliedView"]["sortBy"] == "price"
    assert response.json()["data"]["appliedView"]["transferCounts"] == [0]


def test_view_request_validates_page_size(client_with_session_service: TestClient) -> None:
    response = client_with_session_service.post(
        "/api/v1/journey-search-sessions/session-1/view",
        json={
            "page": 1,
            "page_size": 101,
        },
    )

    assert response.status_code == 422


def test_delete_search_session(client_with_session_service: TestClient) -> None:
    response = client_with_session_service.delete(
        "/api/v1/journey-search-sessions/session-1"
    )

    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True
