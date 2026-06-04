import pytest
from app.models.weather import (
    CurrentWeather,
    HourlyEntry,
    WeatherResponse,
    WMO_CODES,
    get_weather_description,
)


def test_get_weather_description_known_code():
    assert get_weather_description(0) == "Clear sky"
    assert get_weather_description(2) == "Partly cloudy"
    assert get_weather_description(95) == "Thunderstorm"


def test_get_weather_description_unknown_code():
    result = get_weather_description(999)
    assert "999" in result  # fallback includes the code


def test_wmo_codes_has_required_entries():
    required = [0, 1, 2, 3, 45, 48, 51, 53, 55, 61, 63, 65, 71, 73, 75, 80, 81, 82, 95, 96, 99]
    for code in required:
        assert code in WMO_CODES, f"WMO code {code} missing"


def test_weather_response_pydantic_parsing():
    data = {
        "city": "London",
        "latitude": 51.51,
        "longitude": -0.13,
        "current": {
            "temperature_c": 18.2,
            "wind_speed_kmh": 12.4,
            "weather_code": 2,
            "weather_description": "Partly cloudy",
        },
        "hourly": [
            {"hour": "2026-06-04T08:00", "temperature_c": 15.1, "wind_speed_kmh": 9.0}
        ],
        "cached": False,
        "fetched_at": "2026-06-04T14:30:00Z",
    }
    response = WeatherResponse(**data)
    assert response.city == "London"
    assert response.current.temperature_c == 18.2
    assert len(response.hourly) == 1
    assert response.hourly[0].hour == "2026-06-04T08:00"


def test_current_weather_model():
    cw = CurrentWeather(
        temperature_c=20.0,
        wind_speed_kmh=15.0,
        weather_code=3,
        weather_description="Overcast",
    )
    assert cw.temperature_c == 20.0
    assert cw.wind_speed_kmh == 15.0
    assert cw.weather_code == 3
    assert cw.weather_description == "Overcast"


def test_hourly_entry_model():
    entry = HourlyEntry(hour="2026-06-04T10:00", temperature_c=22.5, wind_speed_kmh=8.0)
    assert entry.hour == "2026-06-04T10:00"
    assert entry.temperature_c == 22.5
    assert entry.wind_speed_kmh == 8.0


def test_weather_response_cached_field():
    data = {
        "city": "Paris",
        "latitude": 48.85,
        "longitude": 2.35,
        "current": {
            "temperature_c": 21.0,
            "wind_speed_kmh": 10.0,
            "weather_code": 1,
            "weather_description": "Mainly clear",
        },
        "hourly": [],
        "cached": True,
        "fetched_at": "2026-06-04T12:00:00Z",
    }
    response = WeatherResponse(**data)
    assert response.cached is True
    assert response.city == "Paris"
