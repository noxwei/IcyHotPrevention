"""Voyage AI embedding service with budget protection."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID
import hashlib
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from iety.config import get_settings
from iety.cost.circuit_breaker import BudgetCircuitBreaker, budget_protected
from iety.cost.rate_limiter import rate_limited
from iety.cost.tracker import CostTracker
from iety.processing.chunking import TextChunker, TextChunk

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of an embedding operation."""

    embedding: list[float]
    token_count: int
    content_hash: str
    model: str


class EmbeddingService:
    """Service for generating and storing embeddings using Voyage AI.

    Features:
    - Budget-protected embedding generation
    - Content hash deduplication
    - Batch processing for efficiency
    - Automatic chunking for long texts
    """

    def __init__(
        self,
        session: AsyncSession,
        cost_tracker: Optional[CostTracker] = None,
        circuit_breaker: Optional[BudgetCircuitBreaker] = None,
    ):
        """Initialize embedding service.

        Args:
            session: Database session
            cost_tracker: Cost tracker (creates one if None)
            circuit_breaker: Circuit breaker (creates one if None)
        """
        self.session = session
        self.settings = get_settings().voyage

        if cost_tracker is None:
            cost_tracker = CostTracker(session)
        self.cost_tracker = cost_tracker

        if circuit_breaker is None:
            circuit_breaker = BudgetCircuitBreaker(session)
        self.circuit_breaker = circuit_breaker

        self.chunker = TextChunker(max_tokens=512, overlap_tokens=50)

        # Lazy-load voyageai client
        self._client = None

    @property
    def client(self):
        """Lazy-load Voyage AI client."""
        if self._client is None:
            import voyageai

            api_key = self.settings.api_key
            if api_key is None:
                raise ValueError("VOYAGE_API_KEY not configured")

            self._client = voyageai.Client(api_key=api_key.get_secret_value())
        return self._client

    def _compute_hash(self, text: str) -> str:
        """Compute content hash for deduplication."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    async def _check_existing(self, content_hash: str) -> Optional[list[float]]:
        """Check if embedding already exists for content hash.

        Args:
            content_hash: Hash of the content

        Returns:
            Existing embedding or None
        """
        sql = text("""
            SELECT embedding::text
            FROM integration.embeddings
            WHERE content_hash = :hash
            LIMIT 1
        """)

        result = await self.session.execute(sql, {"hash": content_hash})
        row = result.fetchone()

        if row and row.embedding:
            # Parse vector string to list
            vector_str = row.embedding.strip("[]")
            return [float(x) for x in vector_str.split(",")]

        return None

    @rate_limited("voyage")
    async def _call_voyage_api(self, texts: list[str]) -> tuple[list[list[float]], int]:
        """Call Voyage AI API to generate embeddings.

        Args:
            texts: List of texts to embed

        Returns:
            Tuple of (embeddings, total_tokens)
        """
        result = self.client.embed(
            texts=texts,
            model=self.settings.model,
            input_type="document",
        )

        embeddings = result.embeddings
        total_tokens = result.total_tokens

        return embeddings, total_tokens

    @budget_protected()
    async def embed_texts(
        self,
        texts: list[str],
        skip_existing: bool = True,
    ) -> list[EmbeddingResult]:
        """Generate embeddings for a list of texts.

        Args:
            texts: Texts to embed
            skip_existing: If True, reuse cached embeddings

        Returns:
            List of EmbeddingResult for each text
        """
        results = []
        texts_to_embed = []
        text_indices = []

        # Check for existing embeddings
        for i, text in enumerate(texts):
            content_hash = self._compute_hash(text)

            if skip_existing:
                existing = await self._check_existing(content_hash)
                if existing:
                    results.append(EmbeddingResult(
                        embedding=existing,
                        token_count=self.chunker.count_tokens(text),
                        content_hash=content_hash,
                        model=self.settings.model,
                    ))
                    continue

            texts_to_embed.append(text)
            text_indices.append(i)
            results.append(None)  # Placeholder

        if not texts_to_embed:
            return results

        # Batch API call
        embeddings, total_tokens = await self._call_voyage_api(texts_to_embed)

        # Log cost
        await self.cost_tracker.log_embedding_cost(total_tokens, self.settings.model)

        # Fill in results
        tokens_per_text = total_tokens // len(texts_to_embed)
        for j, (idx, embedding) in enumerate(zip(text_indices, embeddings)):
            content_hash = self._compute_hash(texts_to_embed[j])
            results[idx] = EmbeddingResult(
                embedding=embedding,
                token_count=tokens_per_text,
                content_hash=content_hash,
                model=self.settings.model,
            )

        return results

    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a search query.

        Uses input_type="query" for better search performance.

        Args:
            query: Search query text

        Returns:
            Embedding vector
        """
        # Check budget
        await self.circuit_breaker.check_budget()

        result = self.client.embed(
            texts=[query],
            model=self.settings.model,
            input_type="query",
        )

        # Log cost
        await self.cost_tracker.log_embedding_cost(
            result.total_tokens, self.settings.model
        )

        return result.embeddings[0]

    async def embed_and_store(
        self,
        text: str,
        source_id: UUID,
        source_schema: str,
        source_table: str,
    ) -> list[UUID]:
        """Chunk, embed, and store text in the database.

        Args:
            text: Text to process
            source_id: ID of the source record
            source_schema: Source schema name
            source_table: Source table name

        Returns:
            List of embedding record UUIDs
        """
        # Chunk the text
        chunks = list(self.chunker.chunk_text(text))

        if not chunks:
            return []

        # Generate embeddings for all chunks
        chunk_texts = [c.text for c in chunks]
        embeddings = await self.embed_texts(chunk_texts)

        # Store in database
        embedding_ids = []
        sql = text("""
            INSERT INTO integration.embeddings
                (source_schema, source_table, source_id, content_hash,
                 chunk_index, chunk_text, embedding, model, token_count)
            VALUES
                (:source_schema, :source_table, :source_id, :content_hash,
                 :chunk_index, :chunk_text, :embedding::vector, :model, :token_count)
            ON CONFLICT (source_schema, source_table, source_id, chunk_index)
            DO UPDATE SET
                embedding = EXCLUDED.embedding,
                content_hash = EXCLUDED.content_hash,
                chunk_text = EXCLUDED.chunk_text
            RETURNING id
        """)

        for chunk, emb_result in zip(chunks, embeddings):
            result = await self.session.execute(
                sql,
                {
                    "source_schema": source_schema,
                    "source_table": source_table,
                    "source_id": str(source_id),
                    "content_hash": emb_result.content_hash,
                    "chunk_index": chunk.index,
                    "chunk_text": chunk.text,
                    "embedding": emb_result.embedding,
                    "model": emb_result.model,
                    "token_count": emb_result.token_count,
                },
            )
            row = result.fetchone()
            if row:
                embedding_ids.append(row[0])

        await self.session.commit()
        return embedding_ids

    async def batch_embed_and_store(
        self,
        items: list[dict],
    ) -> int:
        """Batch process multiple items for embedding.

        Args:
            items: List of dicts with keys:
                - text: Text to embed
                - source_id: Source record ID
                - source_schema: Schema name
                - source_table: Table name

        Returns:
            Number of embeddings stored
        """
        total_stored = 0

        # Process in batches to avoid overwhelming API
        batch_size = self.settings.batch_size

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]

            for item in batch:
                try:
                    ids = await self.embed_and_store(
                        text=item["text"],
                        source_id=item["source_id"],
                        source_schema=item["source_schema"],
                        source_table=item["source_table"],
                    )
                    total_stored += len(ids)
                except Exception as e:
                    logger.error(f"Embedding error for {item['source_id']}: {e}")

        return total_stored


async def create_embedding_service(
    session: AsyncSession,
) -> EmbeddingService:
    """Factory function to create embedding service."""
    cost_tracker = CostTracker(session)
    circuit_breaker = BudgetCircuitBreaker(session)
    return EmbeddingService(session, cost_tracker, circuit_breaker)
