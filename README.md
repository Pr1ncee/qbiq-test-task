# Weather Proxy Service

A production-ready REST API proxy for the [Open-Meteo](https://open-meteo.com) public weather provider, with a Vue 3 dashboard frontend. Built with Python 3.12, Flask 3.x (async), Redis caching, and Docker-based deployment.

---

## Table of Contents

- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Local Setup & Running](#local-setup--running)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [CI/CD](#cicd)
- [Assumptions](#assumptions)
- [Improvements Given More Time](#improvements-given-more-time)

---

## Architecture

```
[Browser]
    └── :80  → [nginx / Vue SPA]
                    └── /api/* → [Flask API :5000]
                                      ├── Redis (cache, TTL 10 min)
                                      └── Open-Meteo (external)
```

Three Docker containers, managed by `docker-compose`:

| Service    | Role                                       | Port         |
|------------|--------------------------------------------|--------------|
| `frontend` | nginx serving Vue 3 SPA, proxies `/api/*`  | 80 (public)  |
| `api`      | Flask async REST API                       | 5000 (internal) |
| `redis`    | Cache store (TTL-based, 10-minute default) | 6379 (internal) |

### Flask app layer structure

```
app/
  api/          ← Flask blueprints (routes only, no business logic)
  services/     ← WeatherService (orchestrates cache + client)
  clients/      ← WeatherClient (aiohttp + tenacity retry)
  cache/        ← RedisCache (get/set/TTL wrapper)
  models/       ← Pydantic response and domain models
  middleware/   ← Request ID injection, structured logging setup
  config.py     ← Settings loaded from environment variables
```

### Key technology decisions

| Concern    | Choice                          | Reason                                                 |
|------------|---------------------------------|--------------------------------------------------------|
| Framework  | Flask 3.x + `flask[async]`      | Async views via asgiref; familiar, production-proven   |
| HTTP client | `aiohttp`                      | Non-blocking upstream calls                            |
| Cache      | Redis 7 + `redis-py` (async)    | Fast TTL-based store; required by spec                 |
| Logging    | `structlog`                     | Structured JSON output, context-local `request_id`     |
| Retry      | `tenacity`                      | Declarative retry with exponential backoff             |
| Validation | `pydantic` v2                   | Response models + settings validation                  |
| Frontend   | Vue 3 + Vite + Chart.js         | Lightweight, no heavy UI framework needed              |

---

## API Reference

### `GET /weather?city={city_name}`

Returns current weather conditions and today's hourly forecast for a given city.

**Request flow:**
1. Validate `city` parameter is present (400 if missing)
2. Normalize: strip whitespace, lowercase for cache key
3. Check Redis — cache hit returns response with `X-Cache: HIT`
4. Cache miss → geocode via Open-Meteo geocoding API
5. Fetch current conditions + hourly forecast for today (24h UTC)
6. Store result in Redis with 10-minute TTL
7. Return response with `X-Cache: MISS`

**Response (200):**
```json
{
  "city": "London",
  "latitude": 51.51,
  "longitude": -0.13,
  "current": {
    "temperature_c": 18.2,
    "wind_speed_kmh": 12.4,
    "weather_code": 2,
    "weather_description": "Partly cloudy"
  },
  "hourly": [
    {"hour": "2026-06-04T08:00", "temperature_c": 15.1, "wind_speed_kmh": 9.0}
  ],
  "cached": false,
  "fetched_at": "2026-06-04T14:30:00Z"
}
```

Response header `X-Cache: HIT | MISS` indicates whether the result came from Redis.

### `GET /health`

Returns service health status including Redis connectivity.

**Response (200):**
```json
{"status": "ok", "redis": "ok", "uptime_seconds": 3412}
```

Returns `503` if Redis is unreachable.

### Error responses

All errors follow the same shape:
```json
{"error": "city_not_found", "message": "No results for 'Atlantis'"}
```

| Scenario                         | HTTP status | `error` key           |
|----------------------------------|-------------|-----------------------|
| Missing `city` param             | 400         | `invalid_request`     |
| City not found in geocoding      | 404         | `city_not_found`      |
| Upstream failed after retries    | 502         | `upstream_unavailable` |
| Redis down (health check only)   | 503         | `service_unavailable` |

---

## Local Setup & Running

### Prerequisites

- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed
- No API keys required — Open-Meteo is free and public

### Quickstart (Docker)

```bash
# 1. Clone the repository
git clone <repo-url>
cd <repo-dir>

# 2. Copy and review environment variables (defaults work out of the box)
cp .env.example .env

# 3. Build and start all services
docker-compose up --build
```

The application will be available at **http://localhost**.

The API is accessible directly at **http://localhost/api/weather?city=London**.

### Running without Docker (development)

**Requirements:** Python 3.12, a running Redis instance.

```bash
# Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (edit as needed)
export REDIS_URL=redis://localhost:6379/0
export OPEN_METEO_BASE_URL=https://api.open-meteo.com
export OPEN_METEO_GEO_URL=https://geocoding-api.open-meteo.com
export CACHE_TTL_SECONDS=600
export LOG_LEVEL=info
export PORT=5000

# Start the Flask development server
flask --app app run --port 5000
```

For the frontend in development mode:

```bash
cd frontend
npm install
npm run dev
```

---

## Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` to get started.

| Variable                | Default                                  | Description                          |
|-------------------------|------------------------------------------|--------------------------------------|
| `REDIS_URL`             | `redis://redis:6379/0`                   | Redis connection URL                 |
| `OPEN_METEO_BASE_URL`   | `https://api.open-meteo.com`             | Open-Meteo forecast API base URL     |
| `OPEN_METEO_GEO_URL`    | `https://geocoding-api.open-meteo.com`   | Open-Meteo geocoding API base URL    |
| `CACHE_TTL_SECONDS`     | `600`                                    | Redis cache TTL (10 minutes)         |
| `LOG_LEVEL`             | `info`                                   | Logging level (`debug`, `info`, etc.)|
| `PORT`                  | `5000`                                   | Flask listen port                    |

---

## Project Structure

```
.
├── app/                        # Flask application
│   ├── api/weather.py          # Route handlers (/weather, /health)
│   ├── cache/redis_cache.py    # Redis get/set/TTL wrapper
│   ├── clients/weather_client.py # aiohttp client with tenacity retry
│   ├── middleware/logging.py   # Request ID injection, structlog setup
│   ├── models/weather.py       # Pydantic models + WMO code table
│   ├── services/weather_service.py # Cache-or-fetch orchestration
│   ├── config.py               # Pydantic settings from env vars
│   └── exceptions.py           # CityNotFoundError, UpstreamError
├── frontend/                   # Vue 3 + Vite SPA
│   ├── src/
│   │   ├── components/         # SearchBar, WeatherCard, HourlyChart, etc.
│   │   ├── composables/useWeather.js
│   │   ├── App.vue
│   │   └── main.js
│   ├── Dockerfile              # Multi-stage: Node build → nginx serve
│   └── nginx.conf              # Proxies /api/* to Flask
├── tests/
│   ├── unit/                   # WeatherClient, RedisCache, WeatherService, models
│   └── integration/            # Full API endpoint tests (fakeredis + aioresponses)
├── .github/workflows/ci.yml    # GitHub Actions: lint → test → build
├── Dockerfile                  # Multi-stage Python image
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Observability & Logging

Structured JSON logs are emitted to stdout via `structlog`. Every log line includes `timestamp`, `level`, `request_id`, and `event`.

**Request tracing:**
- Middleware generates a UUID4 `request_id` per request
- Bound into `structlog` context for the entire request lifetime
- Echoed in the `X-Request-ID` response header
- An incoming `X-Request-ID` header is propagated if provided by the caller

**Key logged events:**

| Event                | Fields                               |
|----------------------|--------------------------------------|
| `request_received`   | `method`, `path`                     |
| `request_completed`  | `method`, `path`, `status`, `duration_ms` |
| `cache_hit`          | `city`                               |
| `cache_miss`         | `city`                               |
| `upstream_call`      | `url`, `status`, `duration_ms`       |
| `retry_attempt`      | `attempt`, `error`                   |
| `upstream_error`     | `attempts`, `final_error`            |

---

## Reliability & Resilience

The `WeatherClient` uses **tenacity** for automatic retry with exponential backoff:

- 3 total attempts
- Wait: exponential starting at 0.5s, up to 10s
- Retries on: `aiohttp.ClientError`, HTTP 429, HTTP 5xx
- Does not retry: HTTP 4xx (client errors are non-transient)
- Each retry attempt is logged with attempt number and exception

A circuit breaker (e.g. `pybreaker`) was not included — see [Improvements](#improvements-given-more-time).

---

## Testing

```bash
# Run all tests with coverage
pytest --cov=app --cov-fail-under=85

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

**Dependencies:** `pytest`, `pytest-asyncio`, `pytest-cov`, `fakeredis`, `aioresponses` — no real network calls anywhere in the test suite.

### Unit tests (`tests/unit/`)

| Module           | Scenarios covered                                                         |
|------------------|---------------------------------------------------------------------------|
| `WeatherClient`  | Successful fetch, retry on 5xx, no retry on 4xx, retries exhausted        |
| `RedisCache`     | Cache hit, cache miss, TTL set correctly                                  |
| `WeatherService` | Cache hit path, cache miss + upstream call + store, geocode failure       |
| Response models  | Pydantic parsing of Open-Meteo response shapes, WMO code descriptions    |

### Integration tests (`tests/integration/`)

| Scenario                      | Details                                                     |
|-------------------------------|-------------------------------------------------------------|
| `/weather` happy path (miss)  | `aioresponses` mocks Open-Meteo, `fakeredis` in-memory      |
| `/weather` happy path (hit)   | Pre-populated `fakeredis`, no upstream call                 |
| `/weather` city not found     | Geocoding returns empty results → 404                       |
| `/weather` upstream failure   | All retries exhausted → 502                                 |
| `/weather` missing param      | No `city` parameter → 400                                  |
| `/health` Redis up            | Returns 200 `{"status":"ok","redis":"ok"}`                  |
| `/health` Redis down          | Returns 503                                                 |

---

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and pull request to `main`:

1. **Lint** — `ruff check .` + `ruff format --check .` + `mypy app/`
2. **Test** — `pytest --cov=app --cov-fail-under=85`
3. **Build** — `docker build .`

Steps run sequentially; a lint failure blocks the test run; a test failure blocks the image build.

---

## Assumptions

The following assumptions were made during design and implementation. They are documented here to support discussion in a face-to-face review.

### Weather provider

- **Open-Meteo is used exclusively.** It is free, requires no API key, and has a stable public API. No abstraction layer for multiple providers was introduced because it was not in scope.
- **Geocoding always resolves to the first result.** The Open-Meteo geocoding API may return multiple matches for an ambiguous city name (e.g. "Springfield"). The service picks `results[0]` — the highest-ranked result by population. If this produces wrong results for edge cases, a disambiguation step would be needed.
- **Weather data is fetched at UTC boundaries.** "Today's hourly forecast" means the 24 entries whose ISO timestamp starts with the current UTC date. Users in timezones far from UTC may see tomorrow's data near midnight local time. A per-timezone daily slice was not implemented to keep the API stateless and simple.
- **Current conditions and hourly forecast are always fetched in a single upstream call.** The Open-Meteo `/v1/forecast` endpoint supports both in one request, so no second network round-trip is needed.

### Caching

- **Cache key is `weather:{normalized_city_name}`** where normalized means lowercase + whitespace stripped. "London", "  london  ", and "LONDON" all share the same cache entry. Coordinates returned by geocoding may differ slightly between calls for the same city name (API floating-point variance), but this is acceptable given the 10-minute TTL.
- **The entire response object is cached as JSON.** On a cache hit, the stored payload is deserialized back into the Pydantic model. The `cached: true` flag is set at read time, not stored in Redis, so that a cached response always accurately reports its origin.
- **Redis is treated as a best-effort cache, not a hard dependency for the `/weather` endpoint.** A Redis failure does not cause a 503 for weather requests — the service falls back to a live upstream call. Redis unavailability is only surfaced as a 503 on the `/health` endpoint.
- **No cache invalidation beyond TTL expiry.** Weather data is time-bounded by nature; the 10-minute TTL is an acceptable staleness window for this use case.

### Error handling and resilience

- **4xx responses from Open-Meteo are not retried.** A 404 from geocoding means the city genuinely does not exist; retrying would not help. Only transient conditions (network errors, 429 rate limits, 5xx server errors) trigger the exponential backoff retry.
- **After 3 failed attempts, the service returns 502 to the caller.** The upstream is treated as unavailable; it is the caller's responsibility to retry at the application level if desired.
- **No circuit breaker is implemented.** A circuit breaker (e.g. `pybreaker`) would prevent hammering a fully-down upstream, but adds stateful complexity and is considered an enhancement. The retry-with-backoff strategy is sufficient for occasional transient failures.

### API design

- **No authentication.** The API is intended for internal use behind an nginx reverse proxy. Authentication (API keys, OAuth) was considered out of scope and is listed as a future improvement.
- **`X-Cache` header indicates cache origin.** The `cached` field in the JSON body also carries this information, giving API consumers two ways to detect stale data.
- **The `city` query parameter accepts free-text input.** Validation is limited to checking that the parameter is non-empty. Geocoding handles the interpretation; invalid city names surface as 404 responses.

### Infrastructure

- **Single-command startup: `docker-compose up --build`.** The `api` container waits for the Redis health check before starting, preventing startup failures due to race conditions.
- **The API container runs as a non-root `appuser`.** The multi-stage Dockerfile separates build tools from the runtime image, targeting a ~150 MB final image size.
- **No TLS termination in this setup.** TLS would be handled by a load balancer or ingress controller in a production Kubernetes deployment.
- **Environment variables are the sole configuration mechanism.** No config files are read at runtime; all settings are validated at startup via Pydantic settings.

### Frontend

- **English-only.** No i18n support was implemented.
- **Recent searches are stored in `localStorage`.** Up to the last 5 searched cities are persisted client-side and displayed as clickable chips. No server-side history is stored.
- **`VITE_API_BASE_URL` defaults to `/api`.** This works transparently behind the nginx proxy. For standalone local frontend development, override this to point at `http://localhost:5000`.
- **The chart shows temperature and wind speed on a dual-axis line chart for 24 hourly entries.** Only today's UTC hours are displayed; if fewer than 24 hours remain in the current UTC day, the chart shows only the remaining entries.

---

## Improvements Given More Time

The following enhancements were considered but deliberately deferred to keep the scope focused:

1. **Circuit breaker** (`pybreaker`) — prevent cascading failures when the upstream is fully down; complements the existing retry-with-backoff strategy.
2. **Cache warming** — a background job (e.g. Celery beat) to refresh popular cities before their TTL expires, reducing cold-cache latency spikes.
3. **Rate limiting** (`flask-limiter`) — protect the API from abuse and prevent Open-Meteo rate-limit errors from cascading.
4. **Prometheus metrics + Grafana dashboard** — expose `/metrics` endpoint for request rate, latency percentiles, cache hit ratio, and upstream error rate.
5. **Multi-city comparison** — allow the frontend chart to overlay weather data for multiple cities simultaneously.
6. **API key authentication + usage tracking** — per-client API keys with request quotas; enables SLA enforcement and billing.
7. **Persistent request log storage** (e.g. PostgreSQL) — store anonymized request logs for analytics, trending city queries, and SLA reporting.
8. **Helm chart / Kubernetes manifests** — production-grade deployment with horizontal pod autoscaling, liveness/readiness probes, and a managed Redis (e.g. Elasticache).
9. **OpenTelemetry distributed tracing** — propagate trace context to Open-Meteo calls and Redis operations for end-to-end request tracing in tools like Jaeger or Tempo.
10. **Timezone-aware hourly slices** — accept an optional `tz` query parameter and return the 24-hour window aligned to the user's local date rather than UTC.
11. **Absence of Integration Tests** — no integration tests were developed to preserve simplicity of the system.
