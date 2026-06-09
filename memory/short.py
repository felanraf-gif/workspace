import time
from typing import Any


class ShortMemory:
    def __init__(self, max_size: int = 100):
        self._data: dict[str, Any] = {}
        self._timestamps: dict[str, float] = {}
        self.max_size = max_size

    def store(self, key: str, value: Any, ttl: float = 300.0):
        self._data[key] = value
        self._timestamps[key] = time.time() + ttl
        if len(self._data) > self.max_size:
            oldest = min(self._timestamps, key=self._timestamps.get)
            del self._data[oldest]
            del self._timestamps[oldest]

    def retrieve(self, key: str) -> Any | None:
        ts = self._timestamps.get(key)
        if ts is None:
            return None
        if time.time() > ts:
            del self._data[key]
            del self._timestamps[key]
            return None
        return self._data.get(key)

    def clear(self):
        self._data.clear()
        self._timestamps.clear()
