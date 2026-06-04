from datetime import datetime

from pydantic import BaseModel

WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Heavy freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_weather_description(code: int) -> str:
    return WMO_CODES.get(code, f"Unknown weather code {code}")


class CurrentWeather(BaseModel):
    temperature_c: float
    wind_speed_kmh: float
    weather_code: int
    weather_description: str


class HourlyEntry(BaseModel):
    hour: str  # ISO datetime string e.g. "2026-06-04T08:00"
    temperature_c: float
    wind_speed_kmh: float


class WeatherResponse(BaseModel):
    city: str
    latitude: float
    longitude: float
    current: CurrentWeather
    hourly: list[HourlyEntry]
    cached: bool
    fetched_at: datetime
