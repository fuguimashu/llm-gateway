"""
Passive health checker.
Tracks per-model failure counts. After `fail_threshold` consecutive failures,
the model enters a cooldown period. No active pinging — state is updated
by the proxy service after each request.
"""

import time
from dataclasses import dataclass, field
from threading import Lock

from app.config import config


@dataclass
class ModelHealth:
    consecutive_failures: int = 0
    cooldown_until: float = 0.0  # epoch seconds


class HealthChecker:
    def __init__(self):
        self._lock = Lock()
        self._state: dict[str, ModelHealth] = {}

    def _get(self, model_id: str) -> ModelHealth:
        if model_id not in self._state:
            self._state[model_id] = ModelHealth()
        return self._state[model_id]

    def is_available(self, model_id: str) -> bool:
        with self._lock:
            h = self._get(model_id)
            if h.cooldown_until > time.time():
                return False
            return True

    def record_success(self, model_id: str) -> None:
        with self._lock:
            h = self._get(model_id)
            h.consecutive_failures = 0
            h.cooldown_until = 0.0

    def record_failure(self, model_id: str) -> None:
        with self._lock:
            h = self._get(model_id)
            h.consecutive_failures += 1
            threshold = config.settings.health_fail_threshold
            if h.consecutive_failures >= threshold:
                cooldown = config.settings.health_cooldown_seconds
                h.cooldown_until = time.time() + cooldown

    def get_status(self) -> dict[str, dict]:
        with self._lock:
            now = time.time()
            result = {}
            for model_id, h in self._state.items():
                in_cooldown = h.cooldown_until > now
                result[model_id] = {
                    "available": not in_cooldown,
                    "consecutive_failures": h.consecutive_failures,
                    "cooldown_remaining_seconds": max(0, int(h.cooldown_until - now)) if in_cooldown else 0,
                }
            return result


# Singleton
health_checker = HealthChecker()
