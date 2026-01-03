"""
Unified rate limiting for all platform adapters.
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class RateLimitConfig:
    cooldown_seconds: float = 5.0
    rapid_fire_threshold: int = 5
    rapid_fire_window: int = 60


@dataclass
class RateLimiter:
    config: RateLimitConfig = field(default_factory=RateLimitConfig)
    _user_cooldowns: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    _user_message_times: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def check(self, user_id: str) -> tuple[bool, bool]:
        """
        Check if user is rate limited.
        
        Returns:
            Tuple of (is_limited, is_rapid_fire)
        """
        now = time.time()

        if now - self._user_cooldowns[user_id] < self.config.cooldown_seconds:
            return True, False

        self._user_message_times[user_id] = [
            t for t in self._user_message_times[user_id]
            if now - t < self.config.rapid_fire_window
        ]
        self._user_message_times[user_id].append(now)

        if len(self._user_message_times[user_id]) > self.config.rapid_fire_threshold:
            return True, True

        self._user_cooldowns[user_id] = now
        return False, False

    def reset(self, user_id: str) -> None:
        self._user_cooldowns.pop(user_id, None)
        self._user_message_times.pop(user_id, None)


_default_limiter = RateLimiter()


def is_rate_limited(user_id: str) -> tuple[bool, bool]:
    return _default_limiter.check(user_id)
