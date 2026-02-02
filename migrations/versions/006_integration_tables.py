"""Integration schema tables - entity crosswalk, embeddings, cost tracking, agent memory.

Revision ID: 006
Revises: 005
Create Date: 2024-01-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create entity_identifiers table for cross-domain entity resolution
    op.execute("""
        CREATE TABLE integration.entity_identifiers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            canonical_id UUID NOT NULL,
            entity_type TEXT NOT NULL,
            identifier_type TEXT NOT NULL,
            identifier_value TEXT NOT NULL,
            source_schema TEXT NOT NULL,
            source_table TEXT NOT NULL,
            source_id UUID,
            confidence NUMERIC(3, 2) DEFAULT 1.0,
            verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(identifier_type, identifier_value)
        )
    """)

    # Create canonical_entities table
    op.execute("""
        CREATE TABLE integration.canonical_entities (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_type TEXT NOT NULL,
            canonical_name TEXT NOT NULL,
            aliases JSONB DEFAULT '[]'::jsonb,
            metadata JSONB DEFAULT '{}'::jsonb,
            merged_from UUID[],
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create embeddings table with pgvector
    op.execute("""
        CREATE TABLE integration.embeddings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_schema TEXT NOT NULL,
            source_table TEXT NOT NULL,
            source_id UUID NOT NULL,
            content_hash TEXT NOT NULL,
            chunk_index INTEGER DEFAULT 0,
            chunk_text TEXT NOT NULL,
            embedding vector(1024),
            model TEXT NOT NULL,
            token_count INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(source_schema, source_table, source_id, chunk_index)
        )
    """)

    # Create HNSW index for vector similarity search
    op.execute("""
        CREATE INDEX idx_embeddings_vector ON integration.embeddings
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # Create sync_state table for pipeline checkpoints
    op.execute("""
        CREATE TABLE integration.sync_state (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            pipeline_name TEXT NOT NULL UNIQUE,
            last_sync_at TIMESTAMPTZ,
            checkpoint JSONB NOT NULL DEFAULT '{}'::jsonb,
            records_processed BIGINT DEFAULT 0,
            last_error TEXT,
            last_error_at TIMESTAMPTZ,
            status TEXT DEFAULT 'idle',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create cost_log table for budget tracking
    op.execute("""
        CREATE TABLE integration.cost_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            service TEXT NOT NULL,
            operation TEXT NOT NULL,
            units NUMERIC NOT NULL,
            unit_type TEXT NOT NULL,
            cost_usd NUMERIC(10, 6) NOT NULL,
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create monthly cost summary view
    op.execute("""
        CREATE MATERIALIZED VIEW integration.monthly_cost_summary AS
        SELECT
            date_trunc('month', created_at) AS month,
            service,
            operation,
            SUM(units) AS total_units,
            SUM(cost_usd) AS total_cost,
            COUNT(*) AS request_count
        FROM integration.cost_log
        GROUP BY date_trunc('month', created_at), service, operation
        WITH DATA
    """)

    op.execute("""
        CREATE UNIQUE INDEX idx_monthly_cost_summary
        ON integration.monthly_cost_summary (month, service, operation)
    """)

    # Create agent_memory table for agent personas
    op.execute("""
        CREATE TABLE integration.agent_memory (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent_type TEXT NOT NULL,
            memory_type TEXT NOT NULL,
            content TEXT NOT NULL,
            content_embedding vector(1024),
            context JSONB DEFAULT '{}'::jsonb,
            importance NUMERIC(3, 2) DEFAULT 0.5,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            expires_at TIMESTAMPTZ,
            session_id UUID
        )
    """)

    # Create HNSW index for agent memory search
    op.execute("""
        CREATE INDEX idx_agent_memory_embedding ON integration.agent_memory
        USING hnsw (content_embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # Create agent_sessions table
    op.execute("""
        CREATE TABLE integration.agent_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent_type TEXT NOT NULL,
            started_at TIMESTAMPTZ DEFAULT NOW(),
            ended_at TIMESTAMPTZ,
            context JSONB DEFAULT '{}'::jsonb,
            outcome JSONB,
            token_usage INTEGER DEFAULT 0,
            cost_incurred NUMERIC(10, 6) DEFAULT 0
        )
    """)

    # Create search_log for tracking queries
    op.execute("""
        CREATE TABLE integration.search_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            query TEXT NOT NULL,
            query_embedding vector(1024),
            search_type TEXT NOT NULL,
            filters JSONB DEFAULT '{}'::jsonb,
            result_count INTEGER,
            top_result_ids UUID[],
            latency_ms INTEGER,
            user_feedback JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create indexes
    op.execute("CREATE INDEX idx_entity_identifiers_canonical ON integration.entity_identifiers (canonical_id)")
    op.execute("CREATE INDEX idx_entity_identifiers_type ON integration.entity_identifiers (entity_type, identifier_type)")
    op.execute("CREATE INDEX idx_entity_identifiers_value ON integration.entity_identifiers USING gin (identifier_value gin_trgm_ops)")
    op.execute("CREATE INDEX idx_canonical_entities_name ON integration.canonical_entities USING gin (canonical_name gin_trgm_ops)")
    op.execute("CREATE INDEX idx_canonical_entities_type ON integration.canonical_entities (entity_type)")
    op.execute("CREATE INDEX idx_embeddings_source ON integration.embeddings (source_schema, source_table, source_id)")
    op.execute("CREATE INDEX idx_embeddings_hash ON integration.embeddings (content_hash)")
    op.execute("CREATE INDEX idx_cost_log_service ON integration.cost_log (service, created_at)")
    op.execute("CREATE INDEX idx_cost_log_date ON integration.cost_log (created_at)")
    op.execute("CREATE INDEX idx_agent_memory_type ON integration.agent_memory (agent_type, memory_type)")
    op.execute("CREATE INDEX idx_agent_memory_session ON integration.agent_memory (session_id)")
    op.execute("CREATE INDEX idx_agent_sessions_type ON integration.agent_sessions (agent_type, started_at)")
    op.execute("CREATE INDEX idx_search_log_date ON integration.search_log (created_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS integration.search_log CASCADE")
    op.execute("DROP TABLE IF EXISTS integration.agent_sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS integration.agent_memory CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS integration.monthly_cost_summary CASCADE")
    op.execute("DROP TABLE IF EXISTS integration.cost_log CASCADE")
    op.execute("DROP TABLE IF EXISTS integration.sync_state CASCADE")
    op.execute("DROP TABLE IF EXISTS integration.embeddings CASCADE")
    op.execute("DROP TABLE IF EXISTS integration.entity_identifiers CASCADE")
    op.execute("DROP TABLE IF EXISTS integration.canonical_entities CASCADE")
