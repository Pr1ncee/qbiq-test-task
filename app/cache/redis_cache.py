import json

from redis import Redis


class RedisCache:
    def __init__(self, redis: Redis):
        self._redis = redis

    def get(self, key: str) -> dict | None:
        value = self._redis.get(key)
        if value is None:
            return None
        return json.loads(value)

    def set(self, key: str, value: dict, ttl: int) -> None:
        self._redis.set(key, json.dumps(value, default=str), ex=ttl)

    def ping(self) -> None:
        self._redis.ping()
