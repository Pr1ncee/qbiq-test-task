from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import fakeredis
import pytest

from app.cache.redis_cache import RedisCache
from app.exceptions import CityNotFoundError, UpstreamError
from app.services.weather_service import WeatherService

MOCK_RAW_WEATHER = {
    "current": {
        "temperature_2m": 18.2,
        "wind_speed_10m": 12.4,
        "weather_code": 2,
    },
    "hourly": {
        "time": ["2026-06-04T00:00", "2026-06-04T01:00"],
        "temperature_2m": [15.1, 15.3],
        "wind_speed_10m": [9.0, 9.2],
    },
}


@pytest.fixture
def cache():
    redis = fakeredis.FakeRedis()
    return RedisCache(redis)


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.geocode = AsyncMock(return_value=("London", 51.51, -0.13))
    client.fetch_weather = AsyncMock(return_value=MOCK_RAW_WEATHER)
    return client


@pytest.fixture
def service(cache, mock_client):
    return WeatherService(cache=cache, client=mock_client)


async def test_cache_miss_calls_upstream(service, mock_client):
    result = await service.get_weather("London")
    mock_client.geocode.assert_called_once()
    mock_client.fetch_weather.assert_called_once()
    assert result.city == "London"
    assert result.cached is False


async def test_cache_hit_skips_upstream(service, mock_client):
    # First call populates cache
    await service.get_weather("London")
    mock_client.geocode.reset_mock()
    mock_client.fetch_weather.reset_mock()

    # Second call should hit cache
    result = await service.get_weather("London")
    mock_client.geocode.assert_not_called()
    mock_client.fetch_weather.assert_not_called()
    assert result.cached is True


async def test_city_not_found_propagates(service, mock_client):
    mock_client.geocode.side_effect = CityNotFoundError("No results for 'Atlantis'")
    with pytest.raises(CityNotFoundError):
        await service.get_weather("Atlantis")


async def test_city_normalized_for_cache_key(service, mock_client):
    # "  London  " and "LONDON" should hit the same cache entry
    await service.get_weather("  London  ")
    mock_client.geocode.reset_mock()
    mock_client.fetch_weather.reset_mock()

    result = await service.get_weather("LONDON")
    mock_client.geocode.assert_not_called()  # should be a cache hit
    assert result.cached is True


async def test_response_has_correct_weather_fields(service, mock_client):
    result = await service.get_weather("London")
    assert result.current.temperature_c == 18.2
    assert result.current.wind_speed_kmh == 12.4
    assert result.current.weather_code == 2
    assert result.current.weather_description == "Partly cloudy"


async def test_response_has_coordinates(service, mock_client):
    result = await service.get_weather("London")
    assert result.latitude == 51.51
    assert result.longitude == -0.13


FIXED_TODAY = datetime(2026, 6, 4, 12, 0, 0, tzinfo=timezone.utc)


async def test_hourly_entries_returned(service, mock_client):
    with patch("app.services.weather_service.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-06-04"
        result = await service.get_weather("London")
    assert len(result.hourly) == 2
    assert result.hourly[0].hour == "2026-06-04T00:00"


async def test_upstream_error_propagates(service, mock_client):
    mock_client.fetch_weather.side_effect = UpstreamError("Service unavailable")
    with pytest.raises(UpstreamError):
        await service.get_weather("London")


async def test_geocode_called_with_original_city(service, mock_client):
    # geocode receives the original city string, not the normalized one
    await service.get_weather("  London  ")
    mock_client.geocode.assert_called_once_with("  London  ")


async def test_fetch_weather_called_with_geocoded_coords(service, mock_client):
    await service.get_weather("London")
    mock_client.fetch_weather.assert_called_once_with(51.51, -0.13)
