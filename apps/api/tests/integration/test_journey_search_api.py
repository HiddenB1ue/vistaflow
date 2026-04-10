"""Integration tests for enhanced journey search API endpoint.

Tests the /api/v1/journeys/search endpoint with new features:
- sort_by parameter (duration, price, departure)
- exclude_direct_train_codes_in_transfer_routes
- display_train_types filtering
- Default value behavior
- Parameter validation
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.journeys.dependencies import get_journey_service
from app.journeys.schemas import JourneySearchResponse
from app.main import app


@pytest.fixture
def mock_journey_service():
    """Mock JourneyService for testing API layer."""
    service = MagicMock()
    service.search = AsyncMock()
    return service


@pytest.fixture
def client_with_mock_service(mock_journey_service):
    """Test client with mocked journey service."""
    app.dependency_overrides[get_journey_service] = lambda: mock_journey_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestJourneySearchAPINewFields:
    """Test new API fields added in enhanced journey search."""
    
    def test_sort_by_duration(self, client_with_mock_service, mock_journey_service):
        """Test sort_by='duration' parameter."""
        mock_journey_service.search.return_value = JourneySearchResponse(
            journeys=[],
            total=0,
            date="2024-01-15",
        )
        
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
                "sort_by": "duration",
            },
        )
        
        assert response.status_code == 200
        call_args = mock_journey_service.search.call_args[0][0]
        assert call_args.sort_by == "duration"
    
    def test_sort_by_price(self, client_with_mock_service, mock_journey_service):
        """Test sort_by='price' parameter."""
        mock_journey_service.search.return_value = JourneySearchResponse(
            journeys=[],
            total=0,
            date="2024-01-15",
        )
        
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
                "sort_by": "price",
            },
        )
        
        assert response.status_code == 200
        call_args = mock_journey_service.search.call_args[0][0]
        assert call_args.sort_by == "price"
    
    def test_sort_by_departure(self, client_with_mock_service, mock_journey_service):
        """Test sort_by='departure' parameter."""
        mock_journey_service.search.return_value = JourneySearchResponse(
            journeys=[],
            total=0,
            date="2024-01-15",
        )
        
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
                "sort_by": "departure",
            },
        )
        
        assert response.status_code == 200
        call_args = mock_journey_service.search.call_args[0][0]
        assert call_args.sort_by == "departure"
    
    def test_exclude_direct_train_codes_enabled(self, client_with_mock_service, mock_journey_service):
        """Test exclude_direct_train_codes_in_transfer_routes=true."""
        mock_journey_service.search.return_value = JourneySearchResponse(
            journeys=[],
            total=0,
            date="2024-01-15",
        )
        
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
                "exclude_direct_train_codes_in_transfer_routes": True,
            },
        )
        
        assert response.status_code == 200
        call_args = mock_journey_service.search.call_args[0][0]
        assert call_args.exclude_direct_train_codes_in_transfer_routes is True
    
    def test_display_train_types_filter(self, client_with_mock_service, mock_journey_service):
        """Test display_train_types parameter."""
        mock_journey_service.search.return_value = JourneySearchResponse(
            journeys=[],
            total=0,
            date="2024-01-15",
        )
        
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
                "display_train_types": ["G", "D"],
            },
        )
        
        assert response.status_code == 200
        call_args = mock_journey_service.search.call_args[0][0]
        assert call_args.display_train_types == ["G", "D"]


class TestJourneySearchAPIDefaultValues:
    """Test default values for new and existing fields."""
    
    def test_default_sort_by(self, client_with_mock_service, mock_journey_service):
        """Test that sort_by defaults to 'duration'."""
        mock_journey_service.search.return_value = JourneySearchResponse(
            journeys=[],
            total=0,
            date="2024-01-15",
        )
        
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
            },
        )
        
        assert response.status_code == 200
        call_args = mock_journey_service.search.call_args[0][0]
        assert call_args.sort_by == "duration"
    
    def test_default_train_sequence_top_n(self, client_with_mock_service, mock_journey_service):
        """Test that train_sequence_top_n defaults to 3."""
        mock_journey_service.search.return_value = JourneySearchResponse(
            journeys=[],
            total=0,
            date="2024-01-15",
        )
        
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
            },
        )
        
        assert response.status_code == 200
        call_args = mock_journey_service.search.call_args[0][0]
        assert call_args.train_sequence_top_n == 3
    
    def test_default_exclude_direct_train_codes(self, client_with_mock_service, mock_journey_service):
        """Test that exclude_direct_train_codes_in_transfer_routes defaults to true."""
        mock_journey_service.search.return_value = JourneySearchResponse(
            journeys=[],
            total=0,
            date="2024-01-15",
        )
        
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
            },
        )
        
        assert response.status_code == 200
        call_args = mock_journey_service.search.call_args[0][0]
        assert call_args.exclude_direct_train_codes_in_transfer_routes is True
    
    def test_default_display_limit(self, client_with_mock_service, mock_journey_service):
        """Test that display_limit defaults to 50."""
        mock_journey_service.search.return_value = JourneySearchResponse(
            journeys=[],
            total=0,
            date="2024-01-15",
        )
        
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
            },
        )
        
        assert response.status_code == 200
        call_args = mock_journey_service.search.call_args[0][0]
        assert call_args.display_limit == 50


class TestJourneySearchAPIValidation:
    """Test parameter validation for new fields."""
    
    def test_invalid_sort_by_value(self, client_with_mock_service):
        """Test that invalid sort_by value is rejected."""
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
                "sort_by": "invalid",
            },
        )
        
        assert response.status_code == 422
    
    def test_train_sequence_top_n_out_of_range(self, client_with_mock_service):
        """Test that train_sequence_top_n > 10 is rejected."""
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
                "train_sequence_top_n": 11,
            },
        )
        
        assert response.status_code == 422
    
    def test_display_limit_out_of_range(self, client_with_mock_service):
        """Test that display_limit > 100 is rejected."""
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
                "display_limit": 101,
            },
        )
        
        assert response.status_code == 422


class TestJourneySearchAPIBackwardCompatibility:
    """Test backward compatibility - old requests should work without new fields."""
    
    def test_minimal_request_without_new_fields(self, client_with_mock_service, mock_journey_service):
        """Test that minimal request (without new fields) works correctly."""
        mock_journey_service.search.return_value = JourneySearchResponse(
            journeys=[],
            total=0,
            date="2024-01-15",
        )
        
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # Verify service was called with default values
        call_args = mock_journey_service.search.call_args[0][0]
        assert call_args.sort_by == "duration"
        assert call_args.train_sequence_top_n == 3
        assert call_args.exclude_direct_train_codes_in_transfer_routes is True
    
    def test_legacy_request_with_old_fields_only(self, client_with_mock_service, mock_journey_service):
        """Test that legacy request with old fields only works correctly."""
        mock_journey_service.search.return_value = JourneySearchResponse(
            journeys=[],
            total=0,
            date="2024-01-15",
        )
        
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
                "transfer_count": 1,
                "include_fewer_transfers": True,
                "allowed_train_types": ["G", "D"],
                "min_transfer_minutes": 30,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify old fields are passed correctly
        call_args = mock_journey_service.search.call_args[0][0]
        assert call_args.transfer_count == 1
        assert call_args.include_fewer_transfers is True
        assert call_args.allowed_train_types == ["G", "D"]
        assert call_args.min_transfer_minutes == 30


class TestJourneySearchAPICombinedFeatures:
    """Test combinations of new and existing features."""
    
    def test_combined_filtering_and_sorting(self, client_with_mock_service, mock_journey_service):
        """Test combining train filtering with custom sorting."""
        mock_journey_service.search.return_value = JourneySearchResponse(
            journeys=[],
            total=0,
            date="2024-01-15",
        )
        
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
                "allowed_trains": ["G101", "G201"],
                "sort_by": "price",
                "train_sequence_top_n": 5,
            },
        )
        
        assert response.status_code == 200
        call_args = mock_journey_service.search.call_args[0][0]
        assert call_args.allowed_trains == ["G101", "G201"]
        assert call_args.sort_by == "price"
        assert call_args.train_sequence_top_n == 5
    
    def test_all_new_fields_together(self, client_with_mock_service, mock_journey_service):
        """Test using all new fields together."""
        mock_journey_service.search.return_value = JourneySearchResponse(
            journeys=[],
            total=0,
            date="2024-01-15",
        )
        
        response = client_with_mock_service.post(
            "/api/v1/journeys/search",
            json={
                "from_station": "Beijing",
                "to_station": "Shanghai",
                "date": "2024-01-15",
                "sort_by": "departure",
                "train_sequence_top_n": 2,
                "exclude_direct_train_codes_in_transfer_routes": False,
                "display_train_types": ["G", "D", "C"],
                "display_limit": 30,
            },
        )
        
        assert response.status_code == 200
        call_args = mock_journey_service.search.call_args[0][0]
        assert call_args.sort_by == "departure"
        assert call_args.train_sequence_top_n == 2
        assert call_args.exclude_direct_train_codes_in_transfer_routes is False
        assert call_args.display_train_types == ["G", "D", "C"]
        assert call_args.display_limit == 30
