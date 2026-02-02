"""Cost tracking and budget accounting for IETY."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class CostEntry:
    """A single cost entry."""

    service: str
    operation: str
    units: Decimal
    unit_type: str
    cost_usd: Decimal
    metadata: dict | None = None


@dataclass
class MonthlySummary:
    """Monthly cost summary."""

    month: datetime
    total_cost: Decimal
    budget_limit: Decimal
    budget_percent_used: float
    services: dict[str, Decimal]
    request_count: int


class CostTracker:
    """Tracks API costs and maintains budget accounting."""

    # Cost per unit for each service
    COST_RATES = {
        "voyage": {
            "embed": Decimal("0.00000002"),  # $0.02 per 1M tokens
        },
        "bigquery": {
            "query": Decimal("0.000000005"),  # $5 per TB = $0.000005 per GB
        },
    }

    def __init__(self, session: AsyncSession, monthly_budget: Decimal = Decimal("50.00")):
        self.session = session
        self.monthly_budget = monthly_budget

    async def log_cost(self, entry: CostEntry) -> UUID:
        """Log a cost entry to the database.

        Args:
            entry: Cost entry to log

        Returns:
            UUID of the created log entry
        """
        sql = text("""
            INSERT INTO integration.cost_log
                (service, operation, units, unit_type, cost_usd, metadata)
            VALUES
                (:service, :operation, :units, :unit_type, :cost_usd, :metadata)
            RETURNING id
        """)

        result = await self.session.execute(
            sql,
            {
                "service": entry.service,
                "operation": entry.operation,
                "units": float(entry.units),
                "unit_type": entry.unit_type,
                "cost_usd": float(entry.cost_usd),
                "metadata": entry.metadata or {},
            },
        )
        await self.session.commit()
        row = result.fetchone()
        return row[0] if row else None

    async def log_embedding_cost(
        self, token_count: int, model: str = "voyage-3.5-lite"
    ) -> UUID:
        """Log embedding API cost.

        Args:
            token_count: Number of tokens embedded
            model: Model name

        Returns:
            UUID of the cost log entry
        """
        rate = self.COST_RATES["voyage"]["embed"]
        cost = Decimal(token_count) * rate

        return await self.log_cost(
            CostEntry(
                service="voyage",
                operation="embed",
                units=Decimal(token_count),
                unit_type="tokens",
                cost_usd=cost,
                metadata={"model": model},
            )
        )

    async def log_bigquery_cost(self, bytes_processed: int, query_id: str = "") -> UUID:
        """Log BigQuery cost.

        Args:
            bytes_processed: Bytes processed by the query
            query_id: Optional query identifier

        Returns:
            UUID of the cost log entry
        """
        gb_processed = Decimal(bytes_processed) / Decimal(1024**3)
        rate = self.COST_RATES["bigquery"]["query"]
        cost = gb_processed * rate * Decimal(1024)  # Convert to GB rate

        return await self.log_cost(
            CostEntry(
                service="bigquery",
                operation="query",
                units=gb_processed,
                unit_type="gb",
                cost_usd=cost,
                metadata={"query_id": query_id} if query_id else None,
            )
        )

    async def get_monthly_summary(
        self, month: Optional[datetime] = None
    ) -> MonthlySummary:
        """Get cost summary for a month.

        Args:
            month: Month to get summary for (defaults to current month)

        Returns:
            Monthly cost summary
        """
        if month is None:
            month = datetime.now(timezone.utc).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

        sql = text("""
            SELECT
                service,
                SUM(cost_usd) as total_cost,
                SUM(units) as total_units,
                COUNT(*) as request_count
            FROM integration.cost_log
            WHERE created_at >= :month_start
              AND created_at < :month_start + INTERVAL '1 month'
            GROUP BY service
        """)

        result = await self.session.execute(
            sql, {"month_start": month}
        )
        rows = result.fetchall()

        services = {}
        total_cost = Decimal("0")
        total_requests = 0

        for row in rows:
            service_cost = Decimal(str(row.total_cost))
            services[row.service] = service_cost
            total_cost += service_cost
            total_requests += row.request_count

        budget_percent = float(total_cost / self.monthly_budget) if self.monthly_budget else 0

        return MonthlySummary(
            month=month,
            total_cost=total_cost,
            budget_limit=self.monthly_budget,
            budget_percent_used=budget_percent,
            services=services,
            request_count=total_requests,
        )

    async def get_daily_costs(
        self, days: int = 30
    ) -> list[tuple[datetime, Decimal]]:
        """Get daily cost totals for the last N days.

        Args:
            days: Number of days to retrieve

        Returns:
            List of (date, cost) tuples
        """
        sql = text("""
            SELECT
                DATE(created_at) as day,
                SUM(cost_usd) as daily_cost
            FROM integration.cost_log
            WHERE created_at >= NOW() - :days * INTERVAL '1 day'
            GROUP BY DATE(created_at)
            ORDER BY day DESC
        """)

        result = await self.session.execute(sql, {"days": days})
        return [(row.day, Decimal(str(row.daily_cost))) for row in result]

    async def refresh_monthly_summary_view(self) -> None:
        """Refresh the materialized view for monthly summaries."""
        await self.session.execute(
            text("REFRESH MATERIALIZED VIEW CONCURRENTLY integration.monthly_cost_summary")
        )
        await self.session.commit()
