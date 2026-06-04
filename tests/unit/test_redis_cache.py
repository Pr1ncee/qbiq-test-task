import fakeredis
from app.cache.redis_cache import RedisCache


def make_cache():
    redis = fakeredis.FakeRedis()
    return RedisCache(redis)


def test_cache_miss_returns_none():
    cache = make_cache()
    result = cache.get("nonexistent")
    assert result is None


def test_cache_set_and_get():
    cache = make_cache()
    data = {"city": "London", "temp": 18.2}
    cache.set("weather:london", data, ttl=600)
    result = cache.get("weather:london")
    assert result == data


def test_cache_ttl_is_set():
    cache = make_cache()
    cache.set("weather:paris", {"city": "Paris"}, ttl=300)
    ttl = cache._redis.ttl("weather:paris")
    assert 0 < ttl <= 300


def test_cache_overwrite():
    cache = make_cache()
    cache.set("weather:berlin", {"city": "Berlin", "temp": 10.0}, ttl=600)
    cache.set("weather:berlin", {"city": "Berlin", "temp": 15.0}, ttl=600)
    result = cache.get("weather:berlin")
    assert result["temp"] == 15.0


def test_cache_stores_nested_dict():
    cache = make_cache()
    data = {
        "city": "Tokyo",
        "current": {"temperature_c": 28.0, "wind_speed_kmh": 5.0},
        "hourly": [{"hour": "2026-06-04T09:00", "temperature_c": 25.0}],
    }
    cache.set("weather:tokyo", data, ttl=600)
    result = cache.get("weather:tokyo")
    assert result["current"]["temperature_c"] == 28.0
    assert result["hourly"][0]["hour"] == "2026-06-04T09:00"


def test_cache_ping():
    cache = make_cache()
    cache.ping()


def test_cache_different_keys_are_independent():
    cache = make_cache()
    cache.set("weather:london", {"city": "London"}, ttl=600)
    cache.set("weather:paris", {"city": "Paris"}, ttl=600)
    london = cache.get("weather:london")
    paris = cache.get("weather:paris")
    assert london["city"] == "London"
    assert paris["city"] == "Paris"
