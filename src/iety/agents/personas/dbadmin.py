"""DBAdmin agent persona - database administration and optimization."""

import logging

from iety.agents.base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class DBAdminAgent(BaseAgent):
    """DBAdmin agent responsible for database operations.

    Responsibilities:
    - PostgreSQL schema design and migrations
    - pgvector HNSW index optimization
    - Table partitioning strategies
    - Query performance tuning

    Constraints:
    - Optimize HNSW indexes for low-memory VPS (~1GB RAM)
    - Design for future multi-tenancy (row-level security ready)
    - Use JSONB for flexible schemas, normalize for frequent queries
    """

    @property
    def agent_type(self) -> str:
        return "dbadmin"

    @property
    def system_prompt(self) -> str:
        return """You are @DBAdmin, the database administration agent responsible for:
- PostgreSQL schema design and migrations
- pgvector HNSW index optimization
- Table partitioning strategies
- Query performance tuning

CONSTRAINTS:
- Optimize HNSW indexes for low-memory VPS (~1GB RAM)
- Design for future multi-tenancy (row-level security ready)
- Use JSONB for flexible schemas, normalize for frequent queries

PARTITIONING RULES:
- GDELT events: BY RANGE (sqldate) - monthly partitions
- SEC companyfacts: BY HASH (cik) - 8 partitions
- USASpending awards: BY RANGE (fiscal_year)

INDEX GUIDELINES:
- Use pg_trgm GIN indexes for text search
- HNSW for vector similarity (m=16, ef_construction=64)
- B-tree for exact matches and ranges
- Consider partial indexes for filtered queries

HNSW TUNING (low memory):
- m: 16 (connections per layer)
- ef_construction: 64 (build quality)
- ef_search: 40 (query quality vs speed)

MAINTENANCE:
- VACUUM ANALYZE after bulk loads
- REINDEX for fragmented indexes
- pg_stat_statements for query analysis
"""

    async def execute(self, task: str) -> AgentResult:
        """Execute a database administration task.

        Args:
            task: Task description

        Returns:
            AgentResult with outcome
        """
        # Recall relevant past observations
        memories = await self.recall(task, limit=3)

        # Determine operation type
        operation = self._identify_operation(task)

        # Get operation advice
        advice = self._get_operation_advice(operation)

        # Record observation
        await self.remember(
            f"DBAdmin task: {task} -> Operation: {operation}",
            memory_type="observation",
            importance=0.5,
        )

        return AgentResult(
            status="success",
            outcome={
                "operation": operation,
                "advice": advice,
                "relevant_memories": [m.content for m in memories],
            },
            rationale=f"Identified as {operation} operation",
        )

    def _identify_operation(self, task: str) -> str:
        """Identify operation type from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["schema", "table", "create", "alter"]):
            return "schema"
        elif any(kw in task_lower for kw in ["index", "hnsw", "gin", "btree"]):
            return "indexing"
        elif any(kw in task_lower for kw in ["partition", "split"]):
            return "partitioning"
        elif any(kw in task_lower for kw in ["query", "slow", "performance", "optimize"]):
            return "query_optimization"
        elif any(kw in task_lower for kw in ["vacuum", "analyze", "maintenance"]):
            return "maintenance"
        elif any(kw in task_lower for kw in ["migration", "alembic"]):
            return "migration"
        else:
            return "unknown"

    def _get_operation_advice(self, operation: str) -> dict:
        """Get advice for an operation type."""
        advice = {
            "schema": {
                "guidelines": [
                    "Use UUID for primary keys (gen_random_uuid())",
                    "Add created_at/updated_at timestamps",
                    "Use JSONB for flexible data, normalize hot paths",
                    "Consider future multi-tenancy needs",
                ],
                "example": """
CREATE TABLE schema.table_name (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ...
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
""",
            },
            "indexing": {
                "index_types": {
                    "B-tree": "Default, good for =, <, >, BETWEEN",
                    "GIN": "Full-text search, arrays, JSONB",
                    "GiST": "Geometric data, range types",
                    "HNSW": "Vector similarity (pgvector)",
                },
                "hnsw_config": {
                    "m": 16,
                    "ef_construction": 64,
                    "note": "Lower values for memory-constrained systems",
                },
                "example": """
-- Text search
CREATE INDEX idx_name_trgm ON table USING gin (name gin_trgm_ops);

-- Vector similarity
CREATE INDEX idx_embedding ON table
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
""",
            },
            "partitioning": {
                "strategies": {
                    "RANGE": "Time-series data (dates, fiscal years)",
                    "LIST": "Categorical data (status, type)",
                    "HASH": "Distribute by ID for parallel processing",
                },
                "iety_config": {
                    "gdelt.events": "BY RANGE (month_key) - monthly",
                    "sec.companyfacts": "BY HASH (cik_hash) - 8 partitions",
                    "usaspending.awards": "BY RANGE (fiscal_year)",
                },
            },
            "query_optimization": {
                "steps": [
                    "Run EXPLAIN ANALYZE on slow queries",
                    "Check for sequential scans on large tables",
                    "Verify index usage with pg_stat_user_indexes",
                    "Consider partial indexes for filtered queries",
                    "Use LIMIT with ORDER BY for pagination",
                ],
                "tools": [
                    "pg_stat_statements for query stats",
                    "auto_explain for automatic plan logging",
                    "pg_stat_user_tables for table stats",
                ],
            },
            "maintenance": {
                "tasks": [
                    "VACUUM ANALYZE after bulk loads",
                    "REINDEX for bloated indexes",
                    "Refresh materialized views",
                    "Check for dead tuples",
                ],
                "schedule": {
                    "daily": "VACUUM ANALYZE on active tables",
                    "weekly": "REFRESH MATERIALIZED VIEW",
                    "monthly": "REINDEX on large tables",
                },
            },
            "migration": {
                "tool": "Alembic",
                "guidelines": [
                    "Always test migrations on staging first",
                    "Use online schema changes for large tables",
                    "Include rollback (downgrade) logic",
                    "Version control migration files",
                ],
            },
        }

        return advice.get(operation, {"notes": ["Unknown operation type"]})

    async def get_database_stats(self) -> dict:
        """Get database statistics.

        Returns:
            Dict with database stats
        """
        from sqlalchemy import text

        # Table sizes
        size_sql = text("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as size,
                pg_total_relation_size(schemaname || '.' || tablename) as size_bytes
            FROM pg_tables
            WHERE schemaname IN ('usaspending', 'sec', 'legal', 'gdelt', 'integration')
            ORDER BY size_bytes DESC
            LIMIT 20
        """)

        result = await self.session.execute(size_sql)
        tables = [
            {
                "schema": row.schemaname,
                "table": row.tablename,
                "size": row.size,
            }
            for row in result.fetchall()
        ]

        # Index stats
        index_sql = text("""
            SELECT
                schemaname,
                indexrelname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE schemaname IN ('usaspending', 'sec', 'legal', 'gdelt', 'integration')
            ORDER BY idx_scan DESC
            LIMIT 20
        """)

        result = await self.session.execute(index_sql)
        indexes = [
            {
                "schema": row.schemaname,
                "index": row.indexrelname,
                "scans": row.idx_scan,
            }
            for row in result.fetchall()
        ]

        return {
            "tables": tables,
            "indexes": indexes,
        }
