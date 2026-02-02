"""Unit tests for rate limiter."""

import asyncio
import pytest

from iety.cost.rate_limiter import (
    TokenBucket,
    RateLimitConfig,
    RateLimiterRegistry,
    rate_limited,
    get_rate_limiter_registry,
)


class TestTokenBucket:
    """Tests for TokenBucket rate limiter."""

    @pytest.fixture
    def bucket(self):
        """Create a token bucket."""
        config = RateLimitConfig(name="test", rate=10, period=1.0, burst=10)
        return TokenBucket(config)

    @pytest.mark.asyncio
    async def test_initial_tokens_equal_burst(self, bucket):
        """Bucket should start with burst tokens available."""
        assert bucket.tokens == 10

    @pytest.mark.asyncio
    async def test_acquire_reduces_tokens(self, bucket):
        """Acquiring tokens should reduce available count."""
        await bucket.acquire(3)
        assert bucket.tokens == 7

    @pytest.mark.asyncio
    async def test_try_acquire_success(self, bucket):
        """try_acquire should return True when tokens available."""
        result = await bucket.try_acquire(5)
        assert result is True
        assert bucket.tokens == 5

    @pytest.mark.asyncio
    async def test_try_acquire_failure(self, bucket):
        """try_acquire should return False when insufficient tokens."""
        result = await bucket.try_acquire(15)
        assert result is False
        assert bucket.tokens == 10  # Unchanged

    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self, bucket):
        """Tokens should refill based on rate."""
        await bucket.acquire(10)  # Empty the bucket
        assert bucket.tokens == 0

        # Wait for refill
        await asyncio.sleep(0.5)  # 5 tokens should refill at 10/sec

        # Trigger refill by attempting acquire
        await bucket.try_acquire(0)
        assert bucket.tokens >= 4  # Allow some timing variance

    @pytest.mark.asyncio
    async def test_acquire_waits_when_empty(self, bucket):
        """acquire should wait when tokens unavailable."""
        await bucket.acquire(10)  # Empty

        start = asyncio.get_event_loop().time()
        wait_time = await bucket.acquire(5)  # Should wait for ~0.5s
        end = asyncio.get_event_loop().time()

        assert wait_time > 0
        assert end - start >= 0.4  # Allow some variance


class TestRateLimiterRegistry:
    """Tests for RateLimiterRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry."""
        return RateLimiterRegistry()

    def test_get_creates_limiter(self, registry):
        """get() should create a limiter if it doesn't exist."""
        limiter = registry.get("sec")
        assert limiter is not None
        assert limiter.config.name == "sec"

    def test_get_returns_same_instance(self, registry):
        """get() should return the same instance for repeated calls."""
        limiter1 = registry.get("sec")
        limiter2 = registry.get("sec")
        assert limiter1 is limiter2

    def test_get_unknown_raises_error(self, registry):
        """get() should raise ValueError for unknown limiter names."""
        with pytest.raises(ValueError, match="Unknown rate limiter"):
            registry.get("unknown_limiter")

    def test_register_custom_limiter(self, registry):
        """register() should add custom limiters."""
        config = RateLimitConfig(name="custom", rate=5, period=1.0)
        limiter = registry.register(config)

        assert limiter.config.name == "custom"
        assert registry.get("custom") is limiter

    @pytest.mark.asyncio
    async def test_acquire_delegates_to_limiter(self, registry):
        """acquire() should delegate to the appropriate limiter."""
        await registry.acquire("sec", 1)
        limiter = registry.get("sec")
        assert limiter.tokens == 9  # Started with 10, acquired 1

    def test_stats_returns_limiter_info(self, registry):
        """stats() should return info for all registered limiters."""
        registry.get("sec")
        registry.get("voyage")

        stats = registry.stats()

        assert "sec" in stats
        assert "voyage" in stats
        assert "rate" in stats["sec"]
        assert "available" in stats["sec"]


class TestRateLimitedDecorator:
    """Tests for @rate_limited decorator."""

    @pytest.mark.asyncio
    async def test_decorator_applies_rate_limiting(self):
        """Decorated functions should be rate limited."""
        call_count = 0

        @rate_limited("sec", tokens=1)
        async def limited_function():
            nonlocal call_count
            call_count += 1
            return "result"

        # Call multiple times rapidly
        results = await asyncio.gather(*[limited_function() for _ in range(3)])

        assert all(r == "result" for r in results)
        assert call_count == 3


class TestGlobalRegistry:
    """Tests for global registry."""

    def test_get_rate_limiter_registry_returns_singleton(self):
        """get_rate_limiter_registry should return the same instance."""
        registry1 = get_rate_limiter_registry()
        registry2 = get_rate_limiter_registry()
        assert registry1 is registry2
