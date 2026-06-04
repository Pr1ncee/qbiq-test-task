from datetime import datetime, timezone

import structlog

from app.cache import RedisCache
from app.clients import WeatherClient
from app.config import settings
from app.models import CurrentWeather, HourlyEntry, WeatherResponse, get_weather_description

logger = structlog.get_logger()


class WeatherService:
    def __init__(self, cache: RedisCache, client: WeatherClient):
        self._cache = cache
        self._client = client

    async def get_weather(self, city: str) -> WeatherResponse:
        normalized = city.strip().lower()
        cache_key = f"weather:{normalized}"

        cached_data = self._cache.get(cache_key)
        if cached_data is not None:
            logger.info("cache_hit", city=normalized)
            response = WeatherResponse(**cached_data)
            return response.model_copy(update={"cached": True})

        logger.info("cache_miss", city=normalized)

        display_name, lat, lon = await self._client.geocode(city)
        raw = await self._client.fetch_weather(lat, lon)

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        current_data = raw["current"]
        hourly_data = raw["hourly"]

        current = CurrentWeather(
            temperature_c=current_data["temperature_2m"],
            wind_speed_kmh=current_data["wind_speed_10m"],
            weather_code=current_data["weather_code"],
            weather_description=get_weather_description(current_data["weather_code"]),
        )

        times = hourly_data["time"]
        temps = hourly_data["temperature_2m"]
        winds = hourly_data["wind_speed_10m"]

        hourly = [
            HourlyEntry(hour=t, temperature_c=temp, wind_speed_kmh=wind)
            for t, temp, wind in zip(times, temps, winds)
            if t.startswith(today)
        ]

        weather = WeatherResponse(
            city=display_name,
            latitude=lat,
            longitude=lon,
            current=current,
            hourly=hourly,
            cached=False,
            fetched_at=datetime.now(timezone.utc),
        )

        self._cache.set(cache_key, weather.model_dump(mode="json"), settings.cache_ttl_seconds)

        return weather
