"""Unit tests for budget circuit breaker."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
import pytest

from iety.cost.circuit_breaker import (
    BudgetCircuitBreaker,
    BudgetExceededError,
    BudgetState,
    BudgetStatus,
)


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def circuit_breaker(mock_session):
    """Create a circuit breaker with mock session."""
    return BudgetCircuitBreaker(
        mock_session,
        monthly_budget=Decimal("50.00"),
        warning_threshold=0.90,
        halt_threshold=0.95,
    )


class TestBudgetCircuitBreaker:
    """Tests for BudgetCircuitBreaker."""

    @pytest.mark.asyncio
    async def test_normal_state_when_under_warning(self, circuit_breaker):
        """Circuit breaker should be in NORMAL state when under warning threshold."""
        # Mock the cost tracker to return 40% usage
        circuit_breaker.tracker.get_monthly_summary = AsyncMock(
            return_value=MagicMock(
                total_cost=Decimal("20.00"),
                budget_limit=Decimal("50.00"),
                budget_percent_used=0.40,
            )
        )

        status = await circuit_breaker.get_status()

        assert status.state == BudgetState.NORMAL
        assert status.percent_used == 0.40
        assert status.remaining == Decimal("30.00")

    @pytest.mark.asyncio
    async def test_warning_state_at_threshold(self, circuit_breaker):
        """Circuit breaker should be in WARNING state at 90%."""
        circuit_breaker.tracker.get_monthly_summary = AsyncMock(
            return_value=MagicMock(
                total_cost=Decimal("45.00"),
                budget_limit=Decimal("50.00"),
                budget_percent_used=0.90,
            )
        )

        status = await circuit_breaker.get_status()

        assert status.state == BudgetState.WARNING
        assert status.percent_used == 0.90

    @pytest.mark.asyncio
    async def test_halted_state_at_threshold(self, circuit_breaker):
        """Circuit breaker should be in HALTED state at 95%."""
        circuit_breaker.tracker.get_monthly_summary = AsyncMock(
            return_value=MagicMock(
                total_cost=Decimal("47.50"),
                budget_limit=Decimal("50.00"),
                budget_percent_used=0.95,
            )
        )

        status = await circuit_breaker.get_status()

        assert status.state == BudgetState.HALTED

    @pytest.mark.asyncio
    async def test_check_budget_raises_when_halted(self, circuit_breaker):
        """check_budget should raise BudgetExceededError when halted."""
        circuit_breaker.tracker.get_monthly_summary = AsyncMock(
            return_value=MagicMock(
                total_cost=Decimal("48.00"),
                budget_limit=Decimal("50.00"),
                budget_percent_used=0.96,
            )
        )

        with pytest.raises(BudgetExceededError) as exc_info:
            await circuit_breaker.check_budget()

        assert exc_info.value.current_spend == Decimal("48.00")
        assert exc_info.value.budget_limit == Decimal("50.00")
        assert exc_info.value.percent_used == 0.96

    @pytest.mark.asyncio
    async def test_check_budget_returns_status_when_normal(self, circuit_breaker):
        """check_budget should return status when under threshold."""
        circuit_breaker.tracker.get_monthly_summary = AsyncMock(
            return_value=MagicMock(
                total_cost=Decimal("10.00"),
                budget_limit=Decimal("50.00"),
                budget_percent_used=0.20,
            )
        )

        status = await circuit_breaker.check_budget()

        assert isinstance(status, BudgetStatus)
        assert status.state == BudgetState.NORMAL

    @pytest.mark.asyncio
    async def test_can_spend_returns_true_when_under_limit(self, circuit_breaker):
        """can_spend should return True when projected spend is under halt threshold."""
        circuit_breaker.tracker.get_monthly_summary = AsyncMock(
            return_value=MagicMock(
                total_cost=Decimal("40.00"),
                budget_limit=Decimal("50.00"),
                budget_percent_used=0.80,
            )
        )

        can_spend = await circuit_breaker.can_spend(Decimal("5.00"))

        assert can_spend is True  # 45/50 = 90% < 95%

    @pytest.mark.asyncio
    async def test_can_spend_returns_false_when_would_exceed(self, circuit_breaker):
        """can_spend should return False when projected spend exceeds halt threshold."""
        circuit_breaker.tracker.get_monthly_summary = AsyncMock(
            return_value=MagicMock(
                total_cost=Decimal("45.00"),
                budget_limit=Decimal("50.00"),
                budget_percent_used=0.90,
            )
        )

        can_spend = await circuit_breaker.can_spend(Decimal("5.00"))

        assert can_spend is False  # 50/50 = 100% >= 95%

    @pytest.mark.asyncio
    async def test_state_change_callback_is_called(self, circuit_breaker):
        """State change callbacks should be called when state changes."""
        callback = MagicMock()
        circuit_breaker.on_state_change(callback)

        # First call - sets NORMAL state
        circuit_breaker.tracker.get_monthly_summary = AsyncMock(
            return_value=MagicMock(
                total_cost=Decimal("10.00"),
                budget_limit=Decimal("50.00"),
                budget_percent_used=0.20,
            )
        )
        await circuit_breaker.get_status()

        # Second call - changes to WARNING
        circuit_breaker.tracker.get_monthly_summary = AsyncMock(
            return_value=MagicMock(
                total_cost=Decimal("46.00"),
                budget_limit=Decimal("50.00"),
                budget_percent_used=0.92,
            )
        )
        await circuit_breaker.get_status()

        callback.assert_called_once_with(BudgetState.NORMAL, BudgetState.WARNING)

    @pytest.mark.asyncio
    async def test_guard_context_manager(self, circuit_breaker):
        """guard() context manager should check budget on entry."""
        circuit_breaker.tracker.get_monthly_summary = AsyncMock(
            return_value=MagicMock(
                total_cost=Decimal("10.00"),
                budget_limit=Decimal("50.00"),
                budget_percent_used=0.20,
            )
        )

        async with circuit_breaker.guard() as status:
            assert status.state == BudgetState.NORMAL

    @pytest.mark.asyncio
    async def test_guard_raises_when_halted(self, circuit_breaker):
        """guard() should raise BudgetExceededError when budget is halted."""
        circuit_breaker.tracker.get_monthly_summary = AsyncMock(
            return_value=MagicMock(
                total_cost=Decimal("48.00"),
                budget_limit=Decimal("50.00"),
                budget_percent_used=0.96,
            )
        )

        with pytest.raises(BudgetExceededError):
            async with circuit_breaker.guard():
                pass  # Should not reach here
