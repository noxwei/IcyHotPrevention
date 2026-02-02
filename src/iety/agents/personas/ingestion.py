"""Ingestion agent persona - data pipelines and ETL."""

import logging

from iety.agents.base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class IngestionAgent(BaseAgent):
    """Ingestion agent responsible for data pipelines.

    Responsibilities:
    - Writing Python scripts to fetch data from APIs
    - Implementing rate-limiting decorators (Token Bucket)
    - Managing checkpoint-based resumable pipelines
    - Monitoring data quality and completeness

    Domain Knowledge:
    - USASpending: Account codes 070-0540 for ICE/CBP
    - SEC EDGAR: Mandatory User-Agent header format
    - GDELT: BigQuery requires _PARTITIONDATE filters
    - CourtListener: 5000 req/hour rate limit
    """

    @property
    def agent_type(self) -> str:
        return "ingestion"

    @property
    def system_prompt(self) -> str:
        return """You are @Ingestion, the data engineering agent responsible for:
- Writing Python scripts to fetch data from APIs
- Implementing rate-limiting decorators (Token Bucket)
- Managing checkpoint-based resumable pipelines

KNOWLEDGE:
- USASpending: Account codes 070-0540 for ICE/CBP
- SEC EDGAR: Mandatory User-Agent header format
- GDELT: BigQuery requires _PARTITIONDATE filters
- CourtListener: 5000 req/hour rate limit

Always implement:
1. Exponential backoff for transient failures
2. Checkpoint saving after each batch
3. Rate limiting per API specifications

PIPELINE PATTERN:
```python
async def run(max_batches=None):
    checkpoint = await get_checkpoint()
    while True:
        records, new_checkpoint = await fetch_batch(checkpoint)
        if not records: break
        transformed = [await transform(r) for r in records]
        await upsert(transformed)
        await save_checkpoint(new_checkpoint)
```

RATE LIMITS:
- SEC: 10 requests/second
- CourtListener: 5000 requests/hour
- Voyage AI: 100 requests/second
- USASpending: 100 requests/second
"""

    async def execute(self, task: str) -> AgentResult:
        """Execute an ingestion task.

        Args:
            task: Task description

        Returns:
            AgentResult with outcome
        """
        # Recall relevant past observations
        memories = await self.recall(task, limit=3)

        # Determine pipeline type from task
        pipeline_type = self._identify_pipeline(task)

        # Get pipeline configuration advice
        config_advice = self._get_pipeline_config(pipeline_type)

        # Record observation
        await self.remember(
            f"Ingestion task: {task} -> Pipeline type: {pipeline_type}",
            memory_type="observation",
            importance=0.5,
        )

        return AgentResult(
            status="success",
            outcome={
                "pipeline_type": pipeline_type,
                "configuration": config_advice,
                "relevant_memories": [m.content for m in memories],
            },
            rationale=f"Identified as {pipeline_type} pipeline task",
        )

    def _identify_pipeline(self, task: str) -> str:
        """Identify pipeline type from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["usaspending", "award", "contract", "federal"]):
            return "usaspending"
        elif any(kw in task_lower for kw in ["sec", "edgar", "companyfacts", "cik", "filing"]):
            return "sec"
        elif any(kw in task_lower for kw in ["court", "legal", "docket", "opinion"]):
            return "courtlistener"
        elif any(kw in task_lower for kw in ["gdelt", "event", "news", "global"]):
            return "gdelt"
        else:
            return "unknown"

    def _get_pipeline_config(self, pipeline_type: str) -> dict:
        """Get configuration advice for a pipeline type."""
        configs = {
            "usaspending": {
                "base_url": "https://api.usaspending.gov/api/v2",
                "rate_limit": "100/sec",
                "batch_size": 100,
                "notes": [
                    "Filter by Treasury Account Symbol 070-0540 for ICE",
                    "Supports incremental sync via award_id ordering",
                    "Bulk downloads available for historical data",
                ],
            },
            "sec": {
                "base_url": "https://data.sec.gov",
                "rate_limit": "10/sec",
                "batch_size": 10,
                "notes": [
                    "MANDATORY: Set User-Agent header (name + email)",
                    "CIK must be zero-padded to 10 digits",
                    "companyfacts endpoint returns all XBRL facts",
                ],
            },
            "courtlistener": {
                "base_url": "https://www.courtlistener.com/api/rest/v3",
                "rate_limit": "5000/hour",
                "batch_size": 20,
                "notes": [
                    "Use cursor pagination for large result sets",
                    "API key required for higher limits",
                    "Nature of Suit 462 = Deportation cases",
                ],
            },
            "gdelt": {
                "base_url": "http://data.gdeltproject.org/gdeltv2",
                "rate_limit": "10/sec",
                "batch_size": 1000,
                "notes": [
                    "Updates every 15 minutes",
                    "lastupdate.txt contains latest file URLs",
                    "Filter CAMEO codes for immigration events",
                ],
            },
        }

        return configs.get(pipeline_type, {
            "notes": ["Unknown pipeline type - determine data source first"],
        })

    async def get_sync_status(self) -> dict:
        """Get synchronization status for all pipelines.

        Returns:
            Dict with pipeline statuses
        """
        from sqlalchemy import text

        sql = text("""
            SELECT
                pipeline_name,
                last_sync_at,
                records_processed,
                status,
                last_error,
                last_error_at
            FROM integration.sync_state
            ORDER BY pipeline_name
        """)

        result = await self.session.execute(sql)
        rows = result.fetchall()

        return {
            row.pipeline_name: {
                "last_sync": row.last_sync_at.isoformat() if row.last_sync_at else None,
                "records": row.records_processed,
                "status": row.status,
                "last_error": row.last_error,
            }
            for row in rows
        }
