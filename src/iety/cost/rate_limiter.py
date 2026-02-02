"""Rate limiting for API calls using token bucket algorithm."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for a rate limiter."""

    name: str
    rate: float  # Requests/tokens allowed per period
    period: float = 1.0  # Period in seconds (1.0 = per second, 3600.0 = per hour)
    burst: Optional[float] = None  # Max burst size (defaults to rate)

    def __post_init__(self):
        if self.burst is None:
            self.burst = self.rate


@dataclass
class TokenBucket:
    """Token bucket rate limiter.

    Allows bursting up to `burst` tokens, refilling at `rate` per `period`.
    """

    config: RateLimitConfig
    tokens: float = field(init=False)
    last_refill: float = field(default_factory=time.monotonic)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self):
        self.tokens = self.config.burst

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        refill_amount = elapsed * (self.config.rate / self.config.period)
        self.tokens = min(self.config.burst, self.tokens + refill_amount)
        self.last_refill = now

    async def acquire(self, tokens: float = 1.0) -> float:
        """Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            Time waited in seconds
        """
        async with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0

            # Calculate wait time
            deficit = tokens - self.tokens
            wait_time = deficit * (self.config.period / self.config.rate)

            logger.debug(
                f"Rate limit [{self.config.name}]: waiting {wait_time:.2f}s "
                f"for {tokens} tokens"
            )

            await asyncio.sleep(wait_time)

            self._refill()
            self.tokens -= tokens
            return wait_time

    async def try_acquire(self, tokens: float = 1.0) -> bool:
        """Try to acquire tokens without waiting.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False otherwise
        """
        async with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    @property
    def available(self) -> float:
        """Current available tokens (without refilling)."""
        return self.tokens


# Default rate limit configurations
DEFAULT_RATE_LIMITS = {
    "sec": RateLimitConfig(
        name="sec",
        rate=10,  # 10 requests per second
        period=1.0,
        burst=10,
    ),
    "courtlistener": RateLimitConfig(
        name="courtlistener",
        rate=5000,  # 5000 requests per hour
        period=3600.0,
        burst=100,  # Allow small bursts
    ),
    "voyage": RateLimitConfig(
        name="voyage",
        rate=100,  # 100 requests per second
        period=1.0,
        burst=100,
    ),
    "usaspending": RateLimitConfig(
        name="usaspending",
        rate=100,  # 100 requests per second (generous limit)
        period=1.0,
        burst=50,
    ),
    "gdelt": RateLimitConfig(
        name="gdelt",
        rate=10,  # 10 requests per second for CSV downloads
        period=1.0,
        burst=10,
    ),
}


class RateLimiterRegistry:
    """Registry for managing multiple rate limiters."""

    def __init__(self):
        self._limiters: dict[str, TokenBucket] = {}

    def get(self, name: str) -> TokenBucket:
        """Get or create a rate limiter by name.

        Args:
            name: Rate limiter name (must be in DEFAULT_RATE_LIMITS)

        Returns:
            TokenBucket instance
        """
        if name not in self._limiters:
            if name not in DEFAULT_RATE_LIMITS:
                raise ValueError(f"Unknown rate limiter: {name}")
            self._limiters[name] = TokenBucket(DEFAULT_RATE_LIMITS[name])

        return self._limiters[name]

    def register(self, config: RateLimitConfig) -> TokenBucket:
        """Register a custom rate limiter.

        Args:
            config: Rate limit configuration

        Returns:
            TokenBucket instance
        """
        self._limiters[config.name] = TokenBucket(config)
        return self._limiters[config.name]

    async def acquire(self, name: str, tokens: float = 1.0) -> float:
        """Acquire tokens from a named limiter.

        Args:
            name: Rate limiter name
            tokens: Number of tokens to acquire

        Returns:
            Time waited in seconds
        """
        return await self.get(name).acquire(tokens)

    def stats(self) -> dict[str, dict]:
        """Get stats for all registered limiters."""
        return {
            name: {
                "available": limiter.available,
                "rate": limiter.config.rate,
                "period": limiter.config.period,
                "burst": limiter.config.burst,
            }
            for name, limiter in self._limiters.items()
        }


# Global registry instance
_registry: Optional[RateLimiterRegistry] = None


def get_rate_limiter_registry() -> RateLimiterRegistry:
    """Get the global rate limiter registry."""
    global _registry
    if _registry is None:
        _registry = RateLimiterRegistry()
    return _registry


def rate_limited(limiter_name: str, tokens: float = 1.0):
    """Decorator to rate-limit async functions.

    Args:
        limiter_name: Name of the rate limiter to use
        tokens: Number of tokens per call

    Usage:
        @rate_limited("sec")
        async def fetch_sec_data():
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            registry = get_rate_limiter_registry()
            await registry.acquire(limiter_name, tokens)
            return await func(*args, **kwargs)

        return wrapper
    return decorator
