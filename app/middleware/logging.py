import time
import uuid

import structlog
from flask import Flask, g, request

logger = structlog.get_logger()


def register_middleware(app: Flask) -> None:
    @app.before_request
    def before_request():
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        g.request_id = request_id
        g.start_time = time.time()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        logger.info("request_received", method=request.method, path=request.path)

    @app.after_request
    def after_request(response):
        duration_ms = round((time.time() - g.get("start_time", time.time())) * 1000, 2)
        logger.info(
            "request_completed",
            method=request.method,
            path=request.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Request-ID"] = g.get("request_id", "")
        return response

    @app.teardown_request
    def teardown_request(exc):
        structlog.contextvars.clear_contextvars()
