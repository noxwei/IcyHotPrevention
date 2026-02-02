"""Processor agent persona - ML, embeddings, and search."""

import logging

from iety.agents.base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class ProcessorAgent(BaseAgent):
    """Processor agent responsible for ML and search operations.

    Responsibilities:
    - Text chunking strategies (512 tokens, 50 overlap)
    - Embedding generation with Voyage AI
    - Hybrid search implementation (vector + keyword)
    - Entity resolution with fuzzy matching

    Tools:
    - IBM Docling for PDF table extraction
    - Voyage AI client (voyage-3.5-lite model)
    - PostgreSQL pg_trgm for trigram matching
    """

    @property
    def agent_type(self) -> str:
        return "processor"

    @property
    def system_prompt(self) -> str:
        return """You are @Processor, the ML engineering agent responsible for:
- Text chunking strategies (512 tokens, 50 overlap)
- Embedding generation with Voyage AI
- Hybrid search implementation (vector + keyword)
- Entity resolution with fuzzy matching

TOOLS:
- IBM Docling for PDF table extraction
- Voyage AI client (voyage-3.5-lite model)
- PostgreSQL pg_trgm for trigram matching

COST AWARENESS:
- Track token usage for every embedding call
- Batch embeddings for efficiency (128 texts per call)
- Use content hashing to avoid re-embedding

SEARCH STRATEGY (RRF - Reciprocal Rank Fusion):
- Vector weight: 70%
- Keyword weight: 30%
- RRF formula: 1 / (60 + rank)

CHUNKING RULES:
- Max tokens: 512
- Overlap: 50 tokens
- Prefer sentence boundaries when possible
- Hash content to detect duplicates

ENTITY RESOLUTION:
- pg_trgm similarity threshold: 0.6
- Match by identifier first (UEI, CIK, DUNS)
- Fall back to fuzzy name matching
- Create canonical entities for cross-source linking
"""

    async def execute(self, task: str) -> AgentResult:
        """Execute a processor task.

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
            f"Processing task: {task} -> Operation: {operation}",
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

        if any(kw in task_lower for kw in ["embed", "embedding", "vector"]):
            return "embedding"
        elif any(kw in task_lower for kw in ["search", "query", "find", "retrieve"]):
            return "search"
        elif any(kw in task_lower for kw in ["chunk", "split", "segment"]):
            return "chunking"
        elif any(kw in task_lower for kw in ["entity", "resolve", "match", "link"]):
            return "entity_resolution"
        elif any(kw in task_lower for kw in ["pdf", "document", "extract"]):
            return "document_processing"
        else:
            return "unknown"

    def _get_operation_advice(self, operation: str) -> dict:
        """Get advice for an operation type."""
        advice = {
            "embedding": {
                "model": "voyage-3.5-lite",
                "cost": "$0.02 per 1M tokens",
                "batch_size": 128,
                "steps": [
                    "Check content hash to avoid re-embedding",
                    "Batch texts for efficiency",
                    "Track token usage for cost accounting",
                    "Store embeddings with source references",
                ],
            },
            "search": {
                "strategy": "hybrid (RRF)",
                "weights": {"vector": 0.7, "keyword": 0.3},
                "steps": [
                    "Generate query embedding",
                    "Run vector search with pgvector",
                    "Run keyword search with pg_trgm",
                    "Combine results with RRF",
                    "Log search for analytics",
                ],
            },
            "chunking": {
                "max_tokens": 512,
                "overlap": 50,
                "encoding": "cl100k_base",
                "steps": [
                    "Use tiktoken for accurate token counting",
                    "Prefer sentence boundaries",
                    "Compute content hash for deduplication",
                    "Track chunk indices for context",
                ],
            },
            "entity_resolution": {
                "threshold": 0.6,
                "algorithm": "pg_trgm similarity",
                "steps": [
                    "Try exact identifier match first",
                    "Fall back to fuzzy name matching",
                    "Create canonical entity if new",
                    "Link source records to canonical",
                    "Consider merging similar entities",
                ],
            },
            "document_processing": {
                "tool": "IBM Docling",
                "capabilities": ["PDF extraction", "Table parsing", "OCR"],
                "steps": [
                    "Download document to temp storage",
                    "Extract text and tables with Docling",
                    "Chunk extracted content",
                    "Generate embeddings",
                    "Store with source metadata",
                ],
            },
        }

        return advice.get(operation, {"notes": ["Unknown operation type"]})

    async def estimate_embedding_cost(self, text: str) -> dict:
        """Estimate cost for embedding text.

        Args:
            text: Text to embed

        Returns:
            Cost estimate
        """
        from iety.processing.chunking import TextChunker

        chunker = TextChunker()
        token_count = chunker.count_tokens(text)
        chunks = list(chunker.chunk_text(text))

        # Voyage 3.5 lite: $0.02 per 1M tokens
        cost_per_token = 0.00000002
        estimated_cost = token_count * cost_per_token

        return {
            "token_count": token_count,
            "chunk_count": len(chunks),
            "estimated_cost_usd": estimated_cost,
            "model": "voyage-3.5-lite",
        }
