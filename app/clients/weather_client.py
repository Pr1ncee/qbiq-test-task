import logging
from datetime import datetime, timezone

import aiohttp
from tenacity import (
    RetryError,
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.exceptions import CityNotFoundError, UpstreamError

_std_logger = logging.getLogger(__name__)


def _should_retry(exc: BaseException) -> bool:
    if isinstance(exc, aiohttp.ClientResponseError):
        return exc.status == 429 or exc.status >= 500
    return isinstance(exc, aiohttp.ClientError)


def _make_retry_decorator():
    return retry(
        retry=retry_if_exception(_should_retry),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=0.5, max=10),
        before_sleep=before_sleep_log(_std_logger, logging.WARNING),
    )


class WeatherClient:
    def __init__(self, base_url: str, geo_url: str, session: aiohttp.ClientSession):
        self._base_url = base_url
        self._geo_url = geo_url
        self._session = session

    async def geocode(self, city: str) -> tuple[str, float, float]:
        """Returns (display_name, latitude, longitude). Raises CityNotFoundError if not found."""

        @_make_retry_decorator()
        async def _do_geocode() -> tuple[str, float, float]:
            url = f"{self._geo_url}/v1/search"
            params = {"name": city, "count": 1, "language": "en", "format": "json"}

            async with self._session.get(url, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()

            results = data.get("results", [])
            if not results:
                raise CityNotFoundError(f"No results for '{city}'")

            result = results[0]
            return result["name"], result["latitude"], result["longitude"]

        try:
            return await _do_geocode()
        except CityNotFoundError:
            raise
        except RetryError as e:
            original = e.last_attempt.exception()
            raise UpstreamError(str(original)) from original
        except aiohttp.ClientError as exc:
            raise UpstreamError(f"Geocoding request failed for '{city}'") from exc

    async def fetch_weather(self, lat: float, lon: float) -> dict:
        """Fetch current conditions + today's hourly forecast from Open-Meteo."""

        @_make_retry_decorator()
        async def _do_fetch_weather() -> dict:
            url = f"{self._base_url}/v1/forecast"
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,wind_speed_10m,weather_code",
                "hourly": "temperature_2m,wind_speed_10m",
                "start_date": today,
                "end_date": today,
                "timezone": "UTC",
            }

            async with self._session.get(url, params=params) as resp:
                resp.raise_for_status()
                return await resp.json()

        try:
            return await _do_fetch_weather()
        except RetryError as e:
            original = e.last_attempt.exception()
            raise UpstreamError(str(original)) from original
        except aiohttp.ClientError as exc:
            raise UpstreamError(
                f"Weather fetch request failed for ({lat}, {lon})"
            ) from exc
