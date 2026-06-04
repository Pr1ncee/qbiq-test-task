import json
from typing import cast

from redis import Redis


class RedisCache:
    def __init__(self, redis: Redis):
        self._redis = redis

    def get(self, key: str) -> dict | None:
        raw = self._redis.get(key)
        if raw is None:
            return None
        return json.loads(cast(bytes, raw))

    def set(self, key: str, value: dict, ttl: int) -> None:
        self._redis.set(key, json.dumps(value, default=str), ex=ttl)

    def ping(self) -> None:
        self._redis.ping()
