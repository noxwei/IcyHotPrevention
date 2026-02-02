"""Hybrid search combining vector similarity and keyword matching."""

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from iety.processing.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result."""

    id: UUID
    source_schema: str
    source_table: str
    source_id: UUID
    chunk_index: int
    chunk_text: str
    score: float
    vector_score: Optional[float] = None
    keyword_score: Optional[float] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResponse:
    """Search response with results and metadata."""

    query: str
    results: list[SearchResult]
    total_count: int
    search_type: str  # "vector", "keyword", "hybrid"
    latency_ms: Optional[int] = None


class HybridSearch:
    """Hybrid search combining vector similarity and keyword (trigram) matching.

    Uses Reciprocal Rank Fusion (RRF) to combine scores:
    - Default weights: 70% vector, 30% keyword
    - RRF formula: 1 / (k + rank) where k=60 (standard constant)
    """

    # RRF constant (standard value from literature)
    RRF_K = 60

    def __init__(
        self,
        session: AsyncSession,
        embedding_service: EmbeddingService,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ):
        """Initialize hybrid search.

        Args:
            session: Database session
            embedding_service: Service for generating query embeddings
            vector_weight: Weight for vector search (0-1)
            keyword_weight: Weight for keyword search (0-1)
        """
        self.session = session
        self.embedding_service = embedding_service
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

    async def vector_search(
        self,
        query: str,
        limit: int = 10,
        schema_filter: Optional[str] = None,
        table_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """Pure vector similarity search.

        Args:
            query: Search query
            limit: Maximum results
            schema_filter: Optional schema to filter by
            table_filter: Optional table to filter by

        Returns:
            List of SearchResult ordered by similarity
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_query(query)

        # Build filter conditions
        conditions = []
        params = {
            "query_embedding": query_embedding,
            "limit": limit,
        }

        if schema_filter:
            conditions.append("source_schema = :schema")
            params["schema"] = schema_filter

        if table_filter:
            conditions.append("source_table = :table")
            params["table"] = table_filter

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        sql = text(f"""
            SELECT
                id,
                source_schema,
                source_table,
                source_id,
                chunk_index,
                chunk_text,
                1 - (embedding <=> :query_embedding::vector) as similarity
            FROM integration.embeddings
            {where_clause}
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :limit
        """)

        result = await self.session.execute(sql, params)
        rows = result.fetchall()

        return [
            SearchResult(
                id=row.id,
                source_schema=row.source_schema,
                source_table=row.source_table,
                source_id=row.source_id,
                chunk_index=row.chunk_index,
                chunk_text=row.chunk_text,
                score=float(row.similarity),
                vector_score=float(row.similarity),
            )
            for row in rows
        ]

    async def keyword_search(
        self,
        query: str,
        limit: int = 10,
        schema_filter: Optional[str] = None,
        table_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """Keyword search using PostgreSQL trigram similarity.

        Args:
            query: Search query
            limit: Maximum results
            schema_filter: Optional schema to filter by
            table_filter: Optional table to filter by

        Returns:
            List of SearchResult ordered by trigram similarity
        """
        conditions = ["similarity(chunk_text, :query) > 0.1"]  # Minimum threshold
        params = {
            "query": query,
            "limit": limit,
        }

        if schema_filter:
            conditions.append("source_schema = :schema")
            params["schema"] = schema_filter

        if table_filter:
            conditions.append("source_table = :table")
            params["table"] = table_filter

        where_clause = "WHERE " + " AND ".join(conditions)

        sql = text(f"""
            SELECT
                id,
                source_schema,
                source_table,
                source_id,
                chunk_index,
                chunk_text,
                similarity(chunk_text, :query) as sim_score
            FROM integration.embeddings
            {where_clause}
            ORDER BY sim_score DESC
            LIMIT :limit
        """)

        result = await self.session.execute(sql, params)
        rows = result.fetchall()

        return [
            SearchResult(
                id=row.id,
                source_schema=row.source_schema,
                source_table=row.source_table,
                source_id=row.source_id,
                chunk_index=row.chunk_index,
                chunk_text=row.chunk_text,
                score=float(row.sim_score),
                keyword_score=float(row.sim_score),
            )
            for row in rows
        ]

    def _rrf_score(self, rank: int) -> float:
        """Calculate RRF score for a rank position.

        Args:
            rank: 1-indexed rank position

        Returns:
            RRF score
        """
        return 1.0 / (self.RRF_K + rank)

    async def hybrid_search(
        self,
        query: str,
        limit: int = 10,
        schema_filter: Optional[str] = None,
        table_filter: Optional[str] = None,
    ) -> SearchResponse:
        """Combined vector + keyword search using RRF.

        Args:
            query: Search query
            limit: Maximum results
            schema_filter: Optional schema to filter by
            table_filter: Optional table to filter by

        Returns:
            SearchResponse with ranked results
        """
        import time

        start_time = time.perf_counter()

        # Run both searches (could parallelize)
        vector_results = await self.vector_search(
            query, limit=limit * 2, schema_filter=schema_filter, table_filter=table_filter
        )
        keyword_results = await self.keyword_search(
            query, limit=limit * 2, schema_filter=schema_filter, table_filter=table_filter
        )

        # Build RRF scores
        scores: dict[UUID, dict] = {}

        # Process vector results
        for rank, result in enumerate(vector_results, 1):
            rrf = self._rrf_score(rank) * self.vector_weight
            if result.id not in scores:
                scores[result.id] = {
                    "result": result,
                    "vector_rrf": rrf,
                    "keyword_rrf": 0,
                }
            else:
                scores[result.id]["vector_rrf"] = rrf
            scores[result.id]["result"].vector_score = result.vector_score

        # Process keyword results
        for rank, result in enumerate(keyword_results, 1):
            rrf = self._rrf_score(rank) * self.keyword_weight
            if result.id not in scores:
                scores[result.id] = {
                    "result": result,
                    "vector_rrf": 0,
                    "keyword_rrf": rrf,
                }
            else:
                scores[result.id]["keyword_rrf"] = rrf
            scores[result.id]["result"].keyword_score = result.keyword_score

        # Calculate final scores and sort
        final_results = []
        for item in scores.values():
            result = item["result"]
            result.score = item["vector_rrf"] + item["keyword_rrf"]
            final_results.append(result)

        final_results.sort(key=lambda x: x.score, reverse=True)
        final_results = final_results[:limit]

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return SearchResponse(
            query=query,
            results=final_results,
            total_count=len(final_results),
            search_type="hybrid",
            latency_ms=elapsed_ms,
        )

    async def search(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "hybrid",
        schema_filter: Optional[str] = None,
        table_filter: Optional[str] = None,
    ) -> SearchResponse:
        """Execute search with specified type.

        Args:
            query: Search query
            limit: Maximum results
            search_type: "vector", "keyword", or "hybrid"
            schema_filter: Optional schema to filter by
            table_filter: Optional table to filter by

        Returns:
            SearchResponse with results
        """
        import time

        start_time = time.perf_counter()

        if search_type == "vector":
            results = await self.vector_search(
                query, limit, schema_filter, table_filter
            )
        elif search_type == "keyword":
            results = await self.keyword_search(
                query, limit, schema_filter, table_filter
            )
        else:
            return await self.hybrid_search(
                query, limit, schema_filter, table_filter
            )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return SearchResponse(
            query=query,
            results=results,
            total_count=len(results),
            search_type=search_type,
            latency_ms=elapsed_ms,
        )

    async def log_search(self, response: SearchResponse) -> None:
        """Log search for analytics.

        Args:
            response: Search response to log
        """
        sql = text("""
            INSERT INTO integration.search_log
                (query, search_type, result_count, top_result_ids, latency_ms)
            VALUES
                (:query, :search_type, :result_count, :top_ids, :latency)
        """)

        top_ids = [str(r.id) for r in response.results[:5]]

        await self.session.execute(
            sql,
            {
                "query": response.query,
                "search_type": response.search_type,
                "result_count": response.total_count,
                "top_ids": top_ids,
                "latency": response.latency_ms,
            },
        )
        await self.session.commit()


async def create_hybrid_search(
    session: AsyncSession,
    embedding_service: EmbeddingService,
) -> HybridSearch:
    """Factory function to create hybrid search."""
    return HybridSearch(session, embedding_service)
