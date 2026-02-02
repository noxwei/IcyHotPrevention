"""Budget circuit breaker for cost protection."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Callable, Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from iety.cost.tracker import CostTracker

logger = logging.getLogger(__name__)


class BudgetState(Enum):
    """Budget circuit breaker states."""

    NORMAL = "normal"  # Under warning threshold
    WARNING = "warning"  # Between warning and halt thresholds
    HALTED = "halted"  # At or above halt threshold


class BudgetExceededError(Exception):
    """Raised when budget threshold is exceeded."""

    def __init__(
        self,
        current_spend: Decimal,
        budget_limit: Decimal,
        percent_used: float,
    ):
        self.current_spend = current_spend
        self.budget_limit = budget_limit
        self.percent_used = percent_used
        super().__init__(
            f"Budget exceeded: ${current_spend:.2f} of ${budget_limit:.2f} "
            f"({percent_used:.1%} used)"
        )


@dataclass
class BudgetStatus:
    """Current budget status."""

    state: BudgetState
    current_spend: Decimal
    budget_limit: Decimal
    percent_used: float
    remaining: Decimal
    warning_threshold: float
    halt_threshold: float


class BudgetCircuitBreaker:
    """Circuit breaker that halts API calls when budget is exceeded.

    Usage:
        breaker = BudgetCircuitBreaker(session)

        # Check before making paid API calls
        await breaker.check_budget()  # Raises BudgetExceededError if halted

        # Or use as context manager
        async with breaker.guard():
            await make_api_call()

        # Track callback for monitoring
        breaker.on_state_change(lambda old, new: print(f"{old} -> {new}"))
    """

    def __init__(
        self,
        session: AsyncSession,
        monthly_budget: Decimal = Decimal("50.00"),
        warning_threshold: float = 0.90,
        halt_threshold: float = 0.95,
    ):
        """Initialize the circuit breaker.

        Args:
            session: Database session for cost tracking
            monthly_budget: Monthly budget limit in USD
            warning_threshold: Percentage (0-1) at which to warn
            halt_threshold: Percentage (0-1) at which to halt
        """
        self.tracker = CostTracker(session, monthly_budget)
        self.monthly_budget = monthly_budget
        self.warning_threshold = warning_threshold
        self.halt_threshold = halt_threshold
        self._state = BudgetState.NORMAL
        self._state_callbacks: list[Callable[[BudgetState, BudgetState], None]] = []

    @property
    def state(self) -> BudgetState:
        """Current circuit breaker state."""
        return self._state

    def on_state_change(
        self, callback: Callable[[BudgetState, BudgetState], None]
    ) -> None:
        """Register a callback for state changes.

        Args:
            callback: Function called with (old_state, new_state)
        """
        self._state_callbacks.append(callback)

    def _update_state(self, new_state: BudgetState) -> None:
        """Update state and notify callbacks."""
        if new_state != self._state:
            old_state = self._state
            self._state = new_state
            for callback in self._state_callbacks:
                try:
                    callback(old_state, new_state)
                except Exception as e:
                    logger.error(f"State change callback error: {e}")

    async def get_status(self) -> BudgetStatus:
        """Get current budget status.

        Returns:
            BudgetStatus with current spend and state
        """
        summary = await self.tracker.get_monthly_summary()

        # Determine state based on thresholds
        if summary.budget_percent_used >= self.halt_threshold:
            state = BudgetState.HALTED
        elif summary.budget_percent_used >= self.warning_threshold:
            state = BudgetState.WARNING
        else:
            state = BudgetState.NORMAL

        self._update_state(state)

        return BudgetStatus(
            state=state,
            current_spend=summary.total_cost,
            budget_limit=self.monthly_budget,
            percent_used=summary.budget_percent_used,
            remaining=self.monthly_budget - summary.total_cost,
            warning_threshold=self.warning_threshold,
            halt_threshold=self.halt_threshold,
        )

    async def check_budget(self) -> BudgetStatus:
        """Check budget and raise if exceeded.

        Returns:
            BudgetStatus if within budget

        Raises:
            BudgetExceededError: If budget halt threshold exceeded
        """
        status = await self.get_status()

        if status.state == BudgetState.HALTED:
            logger.error(
                f"Budget HALTED: ${status.current_spend:.2f} of "
                f"${status.budget_limit:.2f} ({status.percent_used:.1%})"
            )
            raise BudgetExceededError(
                status.current_spend,
                status.budget_limit,
                status.percent_used,
            )

        if status.state == BudgetState.WARNING:
            logger.warning(
                f"Budget WARNING: ${status.current_spend:.2f} of "
                f"${status.budget_limit:.2f} ({status.percent_used:.1%})"
            )

        return status

    async def can_spend(self, estimated_cost: Decimal) -> bool:
        """Check if an estimated cost would exceed budget.

        Args:
            estimated_cost: Estimated cost of the operation

        Returns:
            True if the operation can proceed within budget
        """
        status = await self.get_status()
        projected = status.current_spend + estimated_cost
        projected_percent = float(projected / self.monthly_budget)

        return projected_percent < self.halt_threshold

    class _BudgetGuard:
        """Async context manager for budget-protected operations."""

        def __init__(self, breaker: "BudgetCircuitBreaker"):
            self.breaker = breaker

        async def __aenter__(self) -> BudgetStatus:
            return await self.breaker.check_budget()

        async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
            return False

    def guard(self) -> _BudgetGuard:
        """Return a context manager that checks budget on entry.

        Usage:
            async with breaker.guard():
                await make_paid_api_call()
        """
        return self._BudgetGuard(self)


def budget_protected(
    breaker_attr: str = "circuit_breaker",
    estimated_cost: Optional[Decimal] = None,
):
    """Decorator to protect methods with budget checking.

    Args:
        breaker_attr: Attribute name on self that holds the circuit breaker
        estimated_cost: Optional estimated cost to check before execution

    Usage:
        class MyService:
            def __init__(self, session):
                self.circuit_breaker = BudgetCircuitBreaker(session)

            @budget_protected()
            async def make_api_call(self):
                ...
    """
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            breaker: BudgetCircuitBreaker = getattr(self, breaker_attr)

            if estimated_cost is not None:
                if not await breaker.can_spend(estimated_cost):
                    status = await breaker.get_status()
                    raise BudgetExceededError(
                        status.current_spend,
                        status.budget_limit,
                        status.percent_used,
                    )
            else:
                await breaker.check_budget()

            return await func(self, *args, **kwargs)

        return wrapper
    return decorator
