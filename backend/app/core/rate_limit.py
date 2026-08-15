"""Small process-local rate limiter for defensive request throttling."""

from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
import time


class InMemoryRateLimiter:
    """Fixed-window-ish sliding limiter suitable for one local app process."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, *, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(events[0] + window_seconds - now))
                return False, retry_after
            events.append(now)
            return True, 0

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


__all__ = ["InMemoryRateLimiter"]
