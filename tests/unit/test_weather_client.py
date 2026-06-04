import re
import pytest
import aiohttp
from unittest.mock import patch
from aioresponses import aioresponses
import asyncio

from app.clients.weather_client import WeatherClient
from app.exceptions import CityNotFoundError, UpstreamError

GEO_URL = "https://geocoding-api.open-meteo.com"
BASE_URL = "https://api.open-meteo.com"

# Regex patterns to match URLs regardless of query parameter order/presence
GEO_SEARCH_PATTERN = re.compile(r"https://geocoding-api\.open-meteo\.com/v1/search.*")
FORECAST_PATTERN = re.compile(r"https://api\.open-meteo\.com/v1/forecast.*")

GEO_RESPONSE = {
    "results": [{"name": "London", "latitude": 51.51, "longitude": -0.13}]
}

WEATHER_RESPONSE = {
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
async def session():
    async with aiohttp.ClientSession() as s:
        yield s


@pytest.fixture
def client(session):
    return WeatherClient(base_url=BASE_URL, geo_url=GEO_URL, session=session)


async def test_geocode_success(client):
    with aioresponses() as m:
        m.get(GEO_SEARCH_PATTERN, payload=GEO_RESPONSE)
        name, lat, lon = await client.geocode("London")
    assert name == "London"
    assert lat == 51.51
    assert lon == -0.13


async def test_geocode_city_not_found(client):
    with aioresponses() as m:
        m.get(GEO_SEARCH_PATTERN, payload={"results": []})
        with pytest.raises(CityNotFoundError):
            await client.geocode("Atlantis")


async def test_fetch_weather_success(client):
    with aioresponses() as m:
        m.get(FORECAST_PATTERN, payload=WEATHER_RESPONSE)
        result = await client.fetch_weather(51.51, -0.13)
    assert result["current"]["temperature_2m"] == 18.2


async def test_fetch_weather_retries_on_500(client):
    # Patch asyncio.sleep to avoid sleeping between retries in tests
    with patch("asyncio.sleep", return_value=None):
        with aioresponses() as m:
            m.get(FORECAST_PATTERN, status=500)
            m.get(FORECAST_PATTERN, status=500)
            m.get(FORECAST_PATTERN, payload=WEATHER_RESPONSE)
            result = await client.fetch_weather(51.51, -0.13)
    assert result["current"]["temperature_2m"] == 18.2


async def test_fetch_weather_no_retry_on_404(client):
    with aioresponses() as m:
        m.get(FORECAST_PATTERN, status=404)
        with pytest.raises(UpstreamError):
            await client.fetch_weather(51.51, -0.13)
        # Only one request made — if retry happened, aioresponses would raise on the second
        # call since no second mock is registered, so reaching here confirms no retry.


async def test_fetch_weather_exhausted_retries_raises_upstream_error(client):
    # Patch asyncio.sleep to avoid sleeping between retries in tests
    with patch("asyncio.sleep", return_value=None):
        with aioresponses() as m:
            m.get(FORECAST_PATTERN, status=500)
            m.get(FORECAST_PATTERN, status=500)
            m.get(FORECAST_PATTERN, status=500)
            with pytest.raises(UpstreamError):
                await client.fetch_weather(51.51, -0.13)


async def test_geocode_upstream_error_on_500(client):
    with patch("asyncio.sleep", return_value=None):
        with aioresponses() as m:
            m.get(GEO_SEARCH_PATTERN, status=500)
            m.get(GEO_SEARCH_PATTERN, status=500)
            m.get(GEO_SEARCH_PATTERN, status=500)
            with pytest.raises(UpstreamError):
                await client.geocode("London")


async def test_fetch_weather_retries_on_429(client):
    with patch("asyncio.sleep", return_value=None):
        with aioresponses() as m:
            m.get(FORECAST_PATTERN, status=429)
            m.get(FORECAST_PATTERN, payload=WEATHER_RESPONSE)
            result = await client.fetch_weather(51.51, -0.13)
    assert result["current"]["temperature_2m"] == 18.2
