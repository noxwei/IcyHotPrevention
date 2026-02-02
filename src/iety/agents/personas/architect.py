"""Architect agent persona - budget, privacy, and architecture oversight."""

from decimal import Decimal
import logging

from iety.agents.base import BaseAgent, AgentResult
from iety.cost.tracker import CostTracker
from iety.cost.circuit_breaker import BudgetCircuitBreaker

logger = logging.getLogger(__name__)


class ArchitectAgent(BaseAgent):
    """Architect agent responsible for system-wide oversight.

    Responsibilities:
    - Enforcing the <$50/month budget constraint
    - Reviewing code for efficiency and cost optimization
    - Ensuring privacy safeguards (data minimization)
    - Approving architectural decisions
    - Coordinating between other agents

    Has access to:
    - Cost tracking metrics (integration.cost_log)
    - All schema definitions
    - Budget circuit breaker controls
    """

    @property
    def agent_type(self) -> str:
        return "architect"

    @property
    def system_prompt(self) -> str:
        return """You are @Architect, the lead agent responsible for:
- Enforcing the <$50/month budget constraint
- Reviewing code for efficiency and cost optimization
- Ensuring privacy safeguards (data minimization)
- Approving architectural decisions

DIRECTIVE: If a proposed feature requires a monthly subscription >$5,
reject it and propose an open-source alternative.

You have access to:
- Cost tracking metrics (integration.cost_log)
- All schema definitions
- Budget circuit breaker controls

Before approving any change, verify:
1. Estimated monthly cost impact
2. Alignment with data minimization principles
3. No unnecessary API calls or data retention

BUDGET RULES:
- Total monthly limit: $50
- Warning threshold: 90% ($45)
- Halt threshold: 95% ($47.50)

PRIVACY RULES:
- Minimize PII collection
- Prefer aggregated data over individual records
- Implement data retention policies
"""

    def __init__(self, session, memory_store, embedding_service):
        super().__init__(session, memory_store, embedding_service)
        self.cost_tracker = CostTracker(session)
        self.circuit_breaker = BudgetCircuitBreaker(session)

    async def _get_cost_summary(self) -> dict:
        """Get current month's cost summary."""
        summary = await self.cost_tracker.get_monthly_summary()
        return {
            "month": summary.month.isoformat(),
            "total_cost": float(summary.total_cost),
            "budget_limit": float(summary.budget_limit),
            "percent_used": summary.budget_percent_used,
            "remaining": float(summary.budget_limit - summary.total_cost),
            "services": {k: float(v) for k, v in summary.services.items()},
        }

    async def _evaluate_cost_impact(
        self,
        task: str,
        estimated_cost: Decimal,
    ) -> dict:
        """Evaluate if a task's cost is acceptable.

        Args:
            task: Task description
            estimated_cost: Estimated USD cost

        Returns:
            Evaluation result with approval status
        """
        summary = await self._get_cost_summary()
        projected_percent = (
            (summary["total_cost"] + float(estimated_cost))
            / summary["budget_limit"]
        )

        if projected_percent >= 0.95:
            return {
                "approved": False,
                "reason": f"Would exceed halt threshold (projected: {projected_percent:.1%})",
                "recommendation": "Defer to next month or reduce scope",
            }

        if projected_percent >= 0.90:
            return {
                "approved": True,
                "warning": f"Approaching budget limit (projected: {projected_percent:.1%})",
                "recommendation": "Monitor closely, consider deferring non-essential operations",
            }

        return {
            "approved": True,
            "projected_percent": projected_percent,
        }

    async def _review_for_privacy(self, task: str) -> dict:
        """Review task for privacy compliance.

        Args:
            task: Task description

        Returns:
            Privacy review result
        """
        # Keywords that may indicate privacy concerns
        pii_keywords = [
            "personal", "name", "email", "phone", "address", "ssn",
            "social security", "individual", "person", "user",
        ]

        concerns = []
        task_lower = task.lower()

        for keyword in pii_keywords:
            if keyword in task_lower:
                concerns.append(f"Task mentions '{keyword}' - verify data minimization")

        if concerns:
            return {
                "compliant": True,  # Allow but with warnings
                "concerns": concerns,
                "recommendations": [
                    "Aggregate data where possible",
                    "Implement retention limits",
                    "Avoid storing raw PII",
                ],
            }

        return {"compliant": True, "concerns": []}

    async def execute(self, task: str) -> AgentResult:
        """Execute an architect task.

        Args:
            task: Task description

        Returns:
            AgentResult with decision
        """
        # Recall relevant past decisions
        memories = await self.recall(task, limit=3)

        # Get current budget status
        cost_summary = await self._get_cost_summary()

        # Default cost estimate if not specified
        estimated_cost = Decimal("0.01")

        # Evaluate cost impact
        cost_eval = await self._evaluate_cost_impact(task, estimated_cost)

        # Privacy review
        privacy_review = await self._review_for_privacy(task)

        # Make decision
        approved = cost_eval.get("approved", True) and privacy_review.get("compliant", True)

        rationale_parts = []

        if not cost_eval.get("approved"):
            rationale_parts.append(f"Budget: {cost_eval.get('reason')}")
        elif cost_eval.get("warning"):
            rationale_parts.append(f"Budget warning: {cost_eval.get('warning')}")

        if privacy_review.get("concerns"):
            rationale_parts.append(f"Privacy: {', '.join(privacy_review['concerns'])}")

        # Consider past decisions
        for memory in memories:
            if "rejected" in memory.content.lower():
                rationale_parts.append(f"Similar past decision: {memory.content[:100]}")

        rationale = "; ".join(rationale_parts) if rationale_parts else "No concerns identified"

        # Remember this decision
        decision_content = f"Decision on '{task}': {'approved' if approved else 'rejected'} - {rationale}"
        await self.remember(
            decision_content,
            memory_type="decision",
            importance=0.7,
        )

        return AgentResult(
            status="success" if approved else "rejected",
            outcome={
                "approved": approved,
                "cost_summary": cost_summary,
                "cost_evaluation": cost_eval,
                "privacy_review": privacy_review,
            },
            rationale=rationale,
            approved=approved,
        )

    async def get_status_report(self) -> dict:
        """Generate a status report for the system.

        Returns:
            Dict with budget, sync status, and recommendations
        """
        cost_summary = await self._get_cost_summary()
        budget_status = await self.circuit_breaker.get_status()

        return {
            "budget": {
                "current_spend": cost_summary["total_cost"],
                "budget_limit": cost_summary["budget_limit"],
                "percent_used": cost_summary["percent_used"],
                "remaining": cost_summary["remaining"],
                "state": budget_status.state.value,
                "by_service": cost_summary["services"],
            },
            "recommendations": self._generate_recommendations(cost_summary, budget_status),
        }

    def _generate_recommendations(self, cost_summary: dict, budget_status) -> list[str]:
        """Generate recommendations based on current state."""
        recommendations = []

        if budget_status.state.value == "halted":
            recommendations.append("CRITICAL: Budget exceeded - all paid API calls halted")
            recommendations.append("Wait for next month or increase budget limit")
        elif budget_status.state.value == "warning":
            recommendations.append("Budget approaching limit - consider reducing API calls")
            recommendations.append("Prioritize essential operations only")

        # Service-specific recommendations
        for service, cost in cost_summary.get("services", {}).items():
            if cost > 5.0:
                recommendations.append(f"{service}: ${cost:.2f} spent - review usage patterns")

        if not recommendations:
            recommendations.append("System operating within budget - no immediate concerns")

        return recommendations
