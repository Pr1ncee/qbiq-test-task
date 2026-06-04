import threading

import structlog
from flask import Flask
from redis import Redis

from app.cache import RedisCache
from app.config import settings


def create_app() -> Flask:
    app = Flask(__name__)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.ExceptionRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )

    redis_client = Redis.from_url(settings.redis_url)
    app.redis_cache = RedisCache(redis_client)
    app.weather_service = None  # lazily initialized on first async request
    app._service_lock = threading.Lock()

    from app.api import weather_bp

    app.register_blueprint(weather_bp)

    from app.middleware import register_middleware

    register_middleware(app)

    return app
