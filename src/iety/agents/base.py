"""Base agent class with memory interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


@dataclass
class Memory:
    """A single agent memory."""

    content: str
    memory_type: str  # observation, decision, learned_pattern
    importance: float = 0.5
    context: dict = field(default_factory=dict)
    embedding: Optional[list[float]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: UUID = field(default_factory=uuid4)


@dataclass
class AgentContext:
    """Context for an agent session."""

    session_id: UUID
    goal: str
    constraints: list[str] = field(default_factory=list)
    available_tools: list[str] = field(default_factory=list)
    budget_remaining: float = 50.0
    recent_memories: list[Memory] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        goal: str,
        constraints: Optional[list[str]] = None,
        budget_remaining: float = 50.0,
    ) -> "AgentContext":
        """Create a new agent context."""
        return cls(
            session_id=uuid4(),
            goal=goal,
            constraints=constraints or [],
            budget_remaining=budget_remaining,
        )


@dataclass
class AgentResult:
    """Result of an agent task execution."""

    status: str  # success, error, rejected, pending
    outcome: Any = None
    rationale: str = ""
    approved: bool = False
    memories_created: int = 0
    cost_incurred: float = 0.0
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for IETY agents.

    Each agent has:
    - A unique type identifier
    - A system prompt defining its persona
    - Access to memory store for persistence
    - Embedding service for semantic memory retrieval
    - Cost tracking for budget awareness

    Subclasses must implement:
    - agent_type: Unique identifier (architect, ingestion, processor, dbadmin)
    - system_prompt: Persona-specific instructions
    - execute: Task execution logic
    """

    def __init__(
        self,
        session,  # AsyncSession
        memory_store,  # MemoryStore
        embedding_service,  # EmbeddingService
    ):
        """Initialize the agent.

        Args:
            session: Database session
            memory_store: Memory storage service
            embedding_service: Embedding generation service
        """
        self.session = session
        self.memory_store = memory_store
        self.embedding_service = embedding_service
        self.context: Optional[AgentContext] = None

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Unique identifier: architect, ingestion, processor, dbadmin."""
        raise NotImplementedError

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Persona-specific system instructions."""
        raise NotImplementedError

    def set_context(self, context: AgentContext) -> None:
        """Set the agent's current context.

        Args:
            context: Agent context for the session
        """
        self.context = context
        logger.debug(f"[{self.agent_type}] Context set: {context.goal}")

    async def remember(
        self,
        content: str,
        memory_type: str = "observation",
        importance: float = 0.5,
        additional_context: Optional[dict] = None,
    ) -> Memory:
        """Store a memory with semantic embedding.

        Args:
            content: Memory content
            memory_type: Type (observation, decision, learned_pattern)
            importance: Importance score (0-1)
            additional_context: Extra context to store

        Returns:
            Created Memory object
        """
        # Generate embedding for semantic retrieval
        embedding = None
        try:
            if self.embedding_service:
                results = await self.embedding_service.embed_texts([content])
                if results:
                    embedding = results[0].embedding
        except Exception as e:
            logger.warning(f"[{self.agent_type}] Failed to generate embedding: {e}")

        # Build context
        context = {
            "goal": self.context.goal if self.context else None,
            "agent_type": self.agent_type,
        }
        if additional_context:
            context.update(additional_context)

        memory = Memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            context=context,
            embedding=embedding,
        )

        # Persist to database
        if self.memory_store:
            session_id = self.context.session_id if self.context else None
            await self.memory_store.save(self.agent_type, memory, session_id)

        logger.debug(f"[{self.agent_type}] Remembered: {content[:50]}...")
        return memory

    async def recall(
        self,
        query: str,
        limit: int = 5,
        memory_types: Optional[list[str]] = None,
    ) -> list[Memory]:
        """Retrieve relevant memories using semantic search.

        Args:
            query: Search query
            limit: Maximum memories to retrieve
            memory_types: Filter by memory types

        Returns:
            List of relevant memories
        """
        if not self.memory_store:
            return []

        return await self.memory_store.search(
            agent_type=self.agent_type,
            query=query,
            embedding_service=self.embedding_service,
            limit=limit,
            memory_types=memory_types,
        )

    async def reflect(self, recent_limit: int = 20) -> list[str]:
        """Consolidate recent observations into learned patterns.

        Reviews recent observations and extracts patterns that
        should be remembered long-term.

        Args:
            recent_limit: Number of recent observations to analyze

        Returns:
            List of extracted patterns
        """
        if not self.memory_store:
            return []

        # Get recent observations
        recent = await self.memory_store.get_recent(
            agent_type=self.agent_type,
            memory_type="observation",
            limit=recent_limit,
        )

        if len(recent) < 5:
            # Not enough observations to extract patterns
            return []

        # Simple pattern extraction (could be enhanced with LLM)
        patterns = self._extract_patterns(recent)

        # Store patterns as high-importance memories
        for pattern in patterns:
            await self.remember(
                pattern,
                memory_type="learned_pattern",
                importance=0.8,
            )

        return patterns

    def _extract_patterns(self, memories: list[Memory]) -> list[str]:
        """Extract patterns from memories.

        This is a simple implementation that looks for repeated themes.
        Could be enhanced with LLM-based analysis.

        Args:
            memories: List of memories to analyze

        Returns:
            List of pattern strings
        """
        # Count common words/phrases
        word_counts: dict[str, int] = {}
        for memory in memories:
            words = memory.content.lower().split()
            for word in words:
                if len(word) > 5:  # Skip short words
                    word_counts[word] = word_counts.get(word, 0) + 1

        # Find frequently occurring themes
        patterns = []
        for word, count in word_counts.items():
            if count >= len(memories) // 3:  # Appears in 1/3 of memories
                patterns.append(f"Recurring theme: '{word}' observed {count} times")

        return patterns[:5]  # Limit to 5 patterns

    @abstractmethod
    async def execute(self, task: str) -> AgentResult:
        """Execute a task within the agent's domain.

        Args:
            task: Task description

        Returns:
            AgentResult with outcome
        """
        raise NotImplementedError

    async def start_session(self, goal: str, constraints: Optional[list[str]] = None) -> UUID:
        """Start a new agent session.

        Args:
            goal: Session goal
            constraints: Optional constraints

        Returns:
            Session UUID
        """
        context = AgentContext.create(goal, constraints)
        self.set_context(context)

        # Log session start
        if self.memory_store:
            await self.memory_store.start_session(
                agent_type=self.agent_type,
                session_id=context.session_id,
                context={"goal": goal, "constraints": constraints},
            )

        logger.info(f"[{self.agent_type}] Session started: {context.session_id}")
        return context.session_id

    async def end_session(self, outcome: Optional[dict] = None) -> None:
        """End the current agent session.

        Args:
            outcome: Optional outcome data to record
        """
        if not self.context:
            return

        if self.memory_store:
            await self.memory_store.end_session(
                session_id=self.context.session_id,
                outcome=outcome,
            )

        logger.info(f"[{self.agent_type}] Session ended: {self.context.session_id}")
        self.context = None
