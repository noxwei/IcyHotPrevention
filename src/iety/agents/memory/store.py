"""PostgreSQL-backed memory store for agents."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from iety.agents.base import Memory

logger = logging.getLogger(__name__)


class MemoryStore:
    """PostgreSQL-backed memory store for agent personas.

    Stores agent memories with semantic embeddings for retrieval.
    Supports:
    - Save/retrieve memories by agent type
    - Semantic search using pgvector
    - Session tracking
    - Memory consolidation (removing low-importance memories)
    """

    def __init__(self, session: AsyncSession):
        """Initialize memory store.

        Args:
            session: Database session
        """
        self.session = session

    async def save(
        self,
        agent_type: str,
        memory: Memory,
        session_id: Optional[UUID] = None,
    ) -> UUID:
        """Save a memory to the database.

        Args:
            agent_type: Agent type identifier
            memory: Memory to save
            session_id: Optional session ID

        Returns:
            UUID of saved memory
        """
        sql = text("""
            INSERT INTO integration.agent_memory
                (id, agent_type, memory_type, content, content_embedding,
                 context, importance, session_id, created_at)
            VALUES
                (:id, :agent_type, :memory_type, :content, :embedding::vector,
                 :context, :importance, :session_id, :created_at)
            RETURNING id
        """)

        # Convert embedding to string format for PostgreSQL
        embedding_str = None
        if memory.embedding:
            embedding_str = f"[{','.join(str(x) for x in memory.embedding)}]"

        result = await self.session.execute(
            sql,
            {
                "id": str(memory.id),
                "agent_type": agent_type,
                "memory_type": memory.memory_type,
                "content": memory.content,
                "embedding": embedding_str,
                "context": memory.context,
                "importance": memory.importance,
                "session_id": str(session_id) if session_id else None,
                "created_at": memory.created_at,
            },
        )
        await self.session.commit()

        row = result.fetchone()
        return row[0] if row else memory.id

    async def search(
        self,
        agent_type: str,
        query: str,
        embedding_service,
        limit: int = 5,
        memory_types: Optional[list[str]] = None,
    ) -> list[Memory]:
        """Retrieve relevant memories using semantic search.

        Args:
            agent_type: Agent type to search
            query: Search query
            embedding_service: Service for generating query embedding
            limit: Maximum memories to return
            memory_types: Optional filter by memory types

        Returns:
            List of relevant memories
        """
        # Generate query embedding
        query_embedding = await embedding_service.embed_query(query)
        embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

        # Build query with optional type filter
        type_condition = ""
        if memory_types:
            type_list = ", ".join(f"'{t}'" for t in memory_types)
            type_condition = f"AND memory_type IN ({type_list})"

        sql = text(f"""
            SELECT
                id,
                memory_type,
                content,
                context,
                importance,
                created_at,
                1 - (content_embedding <=> :query_embedding::vector) as similarity
            FROM integration.agent_memory
            WHERE agent_type = :agent_type
              AND content_embedding IS NOT NULL
              AND (expires_at IS NULL OR expires_at > NOW())
              {type_condition}
            ORDER BY content_embedding <=> :query_embedding::vector
            LIMIT :limit
        """)

        result = await self.session.execute(
            sql,
            {
                "agent_type": agent_type,
                "query_embedding": embedding_str,
                "limit": limit,
            },
        )

        memories = []
        for row in result.fetchall():
            memories.append(
                Memory(
                    id=row.id,
                    content=row.content,
                    memory_type=row.memory_type,
                    importance=float(row.importance),
                    context=row.context or {},
                    created_at=row.created_at,
                )
            )

        return memories

    async def get_recent(
        self,
        agent_type: str,
        memory_type: Optional[str] = None,
        limit: int = 20,
        since: Optional[datetime] = None,
    ) -> list[Memory]:
        """Get recent memories by creation time.

        Args:
            agent_type: Agent type
            memory_type: Optional filter by type
            limit: Maximum memories
            since: Optional datetime filter

        Returns:
            List of recent memories
        """
        conditions = ["agent_type = :agent_type"]
        params = {"agent_type": agent_type, "limit": limit}

        if memory_type:
            conditions.append("memory_type = :memory_type")
            params["memory_type"] = memory_type

        if since:
            conditions.append("created_at >= :since")
            params["since"] = since

        where_clause = " AND ".join(conditions)

        sql = text(f"""
            SELECT id, memory_type, content, context, importance, created_at
            FROM integration.agent_memory
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
        """)

        result = await self.session.execute(sql, params)

        return [
            Memory(
                id=row.id,
                content=row.content,
                memory_type=row.memory_type,
                importance=float(row.importance),
                context=row.context or {},
                created_at=row.created_at,
            )
            for row in result.fetchall()
        ]

    async def consolidate(
        self,
        agent_type: str,
        importance_threshold: float = 0.3,
        days_old: int = 7,
    ) -> int:
        """Remove low-importance memories older than threshold.

        Args:
            agent_type: Agent type
            importance_threshold: Remove memories below this importance
            days_old: Only remove memories older than this

        Returns:
            Number of memories removed
        """
        sql = text("""
            DELETE FROM integration.agent_memory
            WHERE agent_type = :agent_type
              AND importance < :threshold
              AND created_at < NOW() - :days * INTERVAL '1 day'
            RETURNING id
        """)

        result = await self.session.execute(
            sql,
            {
                "agent_type": agent_type,
                "threshold": importance_threshold,
                "days": days_old,
            },
        )
        await self.session.commit()

        deleted = len(result.fetchall())
        logger.info(f"Consolidated {deleted} memories for {agent_type}")
        return deleted

    async def start_session(
        self,
        agent_type: str,
        session_id: UUID,
        context: Optional[dict] = None,
    ) -> None:
        """Record a new agent session.

        Args:
            agent_type: Agent type
            session_id: Session UUID
            context: Initial session context
        """
        sql = text("""
            INSERT INTO integration.agent_sessions
                (id, agent_type, context, started_at)
            VALUES
                (:id, :agent_type, :context, NOW())
        """)

        await self.session.execute(
            sql,
            {
                "id": str(session_id),
                "agent_type": agent_type,
                "context": context or {},
            },
        )
        await self.session.commit()

    async def end_session(
        self,
        session_id: UUID,
        outcome: Optional[dict] = None,
        token_usage: int = 0,
        cost_incurred: float = 0.0,
    ) -> None:
        """Mark a session as ended.

        Args:
            session_id: Session UUID
            outcome: Session outcome data
            token_usage: Total tokens used
            cost_incurred: Total cost incurred
        """
        sql = text("""
            UPDATE integration.agent_sessions
            SET
                ended_at = NOW(),
                outcome = :outcome,
                token_usage = :token_usage,
                cost_incurred = :cost_incurred
            WHERE id = :id
        """)

        await self.session.execute(
            sql,
            {
                "id": str(session_id),
                "outcome": outcome or {},
                "token_usage": token_usage,
                "cost_incurred": cost_incurred,
            },
        )
        await self.session.commit()

    async def get_session_memories(
        self,
        session_id: UUID,
    ) -> list[Memory]:
        """Get all memories from a specific session.

        Args:
            session_id: Session UUID

        Returns:
            List of memories from the session
        """
        sql = text("""
            SELECT id, memory_type, content, context, importance, created_at
            FROM integration.agent_memory
            WHERE session_id = :session_id
            ORDER BY created_at ASC
        """)

        result = await self.session.execute(sql, {"session_id": str(session_id)})

        return [
            Memory(
                id=row.id,
                content=row.content,
                memory_type=row.memory_type,
                importance=float(row.importance),
                context=row.context or {},
                created_at=row.created_at,
            )
            for row in result.fetchall()
        ]
