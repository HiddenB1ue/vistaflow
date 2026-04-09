from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.integrations.geo.client import AmapGeoClient, GeoAuthError, GeoRateLimitError


def _make_response(payload: dict[str, object]) -> MagicMock:
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


@pytest.mark.asyncio
async def test_geocode_address_uses_address_param_only() -> None:
    http_client = AsyncMock()
    http_client.get.return_value = _make_response(
        {"status": "1", "geocodes": [{"location": "121.327512,31.200759"}]}
    )
    client = AmapGeoClient(api_key="demo-key", http_client=http_client)

    result = await client.geocode_address("上海虹桥站")

    assert result == (121.327512, 31.200759)
    params = http_client.get.await_args.kwargs["params"]
    assert params["address"] == "上海虹桥站"
    assert "city" not in params


@pytest.mark.asyncio
async def test_geocode_address_returns_none_when_no_geocodes() -> None:
    http_client = AsyncMock()
    http_client.get.return_value = _make_response({"status": "1", "geocodes": []})
    client = AmapGeoClient(api_key="demo-key", http_client=http_client)

    result = await client.geocode_address("未知地址")

    assert result is None


@pytest.mark.asyncio
async def test_geocode_address_returns_none_for_malformed_location() -> None:
    http_client = AsyncMock()
    http_client.get.return_value = _make_response(
        {"status": "1", "geocodes": [{"location": "121.327512"}]}
    )
    client = AmapGeoClient(api_key="demo-key", http_client=http_client)

    result = await client.geocode_address("上海虹桥站")

    assert result is None


@pytest.mark.asyncio
async def test_geocode_address_retries_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    http_client = AsyncMock()
    http_client.get.side_effect = [
        _make_response({"status": "0", "infocode": "10021", "info": "RATE_LIMIT"}),
        _make_response({"status": "1", "geocodes": [{"location": "121.327512,31.200759"}]}),
    ]
    sleep = AsyncMock()
    monkeypatch.setattr("app.integrations.geo.client.asyncio.sleep", sleep)
    client = AmapGeoClient(api_key="demo-key", http_client=http_client)

    result = await client.geocode_address("上海虹桥站")

    assert result == (121.327512, 31.200759)
    sleep.assert_awaited_once()


@pytest.mark.asyncio
async def test_geocode_address_raises_on_auth_error() -> None:
    http_client = AsyncMock()
    http_client.get.return_value = _make_response(
        {"status": "0", "infocode": "10009", "info": "INVALID_USER_KEY"}
    )
    client = AmapGeoClient(api_key="demo-key", http_client=http_client)

    with pytest.raises(GeoAuthError):
        await client.geocode_address("上海虹桥站")


@pytest.mark.asyncio
async def test_geocode_address_raises_after_rate_limit_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    http_client = AsyncMock()
    http_client.get.side_effect = [
        _make_response({"status": "0", "infocode": "10021", "info": "RATE_LIMIT"}),
        _make_response({"status": "0", "infocode": "10021", "info": "RATE_LIMIT"}),
    ]
    sleep = AsyncMock()
    monkeypatch.setattr("app.integrations.geo.client.asyncio.sleep", sleep)
    client = AmapGeoClient(
        api_key="demo-key",
        http_client=http_client,
        max_retries=2,
    )

    with pytest.raises(GeoRateLimitError):
        await client.geocode_address("上海虹桥站")

    assert sleep.await_count == 1
