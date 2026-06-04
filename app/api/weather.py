import time

import aiohttp
import structlog
from flask import Blueprint, current_app, jsonify, request

from app.clients import WeatherClient
from app.config import settings
from app.exceptions import CityNotFoundError, UpstreamError
from app.services import WeatherService

logger = structlog.get_logger()
weather_bp = Blueprint("weather", __name__)

_start_time = time.time()


async def _get_service() -> WeatherService:
    if current_app.weather_service is None:
        with current_app._service_lock:
            if current_app.weather_service is None:
                session = aiohttp.ClientSession()
                client = WeatherClient(
                    base_url=settings.open_meteo_base_url,
                    geo_url=settings.open_meteo_geo_url,
                    session=session,
                )
                current_app.weather_service = WeatherService(
                    cache=current_app.redis_cache,
                    client=client,
                )
    return current_app.weather_service


@weather_bp.get("/weather")
async def get_weather():
    city = request.args.get("city", "").strip()
    if not city:
        return jsonify({"error": "invalid_request", "message": "Missing required parameter: city"}), 400

    try:
        service = await _get_service()
        weather = await service.get_weather(city)
        response = jsonify(weather.model_dump(mode="json"))
        response.headers["X-Cache"] = "HIT" if weather.cached else "MISS"
        return response
    except CityNotFoundError as e:
        return jsonify({"error": "city_not_found", "message": str(e)}), 404
    except UpstreamError as e:
        return jsonify({"error": "upstream_unavailable", "message": str(e)}), 502
    except Exception as e:
        logger.error("unexpected_error", error=str(e), exc_info=True)
        return jsonify({"error": "internal_error", "message": "An unexpected error occurred"}), 500


@weather_bp.get("/health")
async def health():
    uptime = round(time.time() - _start_time)
    try:
        current_app.redis_cache.ping()
        return jsonify({"status": "ok", "redis": "ok", "uptime_seconds": uptime})
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        return jsonify({
            "error": "service_unavailable",
            "message": "Redis is unreachable",
            "status": "error",
            "redis": "error",
            "uptime_seconds": uptime,
        }), 503
