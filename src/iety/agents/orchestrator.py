"""Multi-agent orchestrator for coordinating agent tasks."""

from typing import Optional
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from iety.agents.base import BaseAgent, AgentResult, AgentContext
from iety.agents.memory.store import MemoryStore
from iety.agents.personas.architect import ArchitectAgent
from iety.agents.personas.ingestion import IngestionAgent
from iety.agents.personas.processor import ProcessorAgent
from iety.agents.personas.dbadmin import DBAdminAgent

logger = logging.getLogger(__name__)


# Agent type registry
AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "architect": ArchitectAgent,
    "ingestion": IngestionAgent,
    "processor": ProcessorAgent,
    "dbadmin": DBAdminAgent,
}


class AgentOrchestrator:
    """Orchestrator for coordinating multiple agent personas.

    Responsibilities:
    - Creating and managing agent instances
    - Routing tasks to appropriate agents
    - Enforcing architect approval for changes
    - Handling inter-agent handoffs
    """

    def __init__(
        self,
        session: AsyncSession,
        memory_store: MemoryStore,
        embedding_service,
        cost_tracker=None,
    ):
        """Initialize the orchestrator.

        Args:
            session: Database session
            memory_store: Memory storage service
            embedding_service: Embedding generation service
            cost_tracker: Optional cost tracker
        """
        self.session = session
        self.memory_store = memory_store
        self.embedding_service = embedding_service
        self.cost_tracker = cost_tracker
        self._agents: dict[str, BaseAgent] = {}

    def get_agent(self, agent_type: str) -> BaseAgent:
        """Get or create an agent by type.

        Args:
            agent_type: Agent type identifier

        Returns:
            Agent instance

        Raises:
            ValueError: If agent type is unknown
        """
        if agent_type not in AGENT_REGISTRY:
            raise ValueError(f"Unknown agent type: {agent_type}")

        if agent_type not in self._agents:
            agent_cls = AGENT_REGISTRY[agent_type]
            self._agents[agent_type] = agent_cls(
                self.session,
                self.memory_store,
                self.embedding_service,
            )

        return self._agents[agent_type]

    async def delegate(
        self,
        task: str,
        agent_type: str,
        require_approval: bool = True,
    ) -> AgentResult:
        """Delegate a task to a specific agent.

        If require_approval is True and the agent is not the architect,
        the architect will review the task first.

        Args:
            task: Task description
            agent_type: Target agent type
            require_approval: Whether to require architect approval

        Returns:
            AgentResult from the executing agent
        """
        agent = self.get_agent(agent_type)

        # Architect approval for non-architect tasks
        if require_approval and agent_type != "architect":
            architect = self.get_agent("architect")
            approval = await architect.execute(f"Approve task for @{agent_type}: {task}")

            if not approval.approved:
                logger.warning(
                    f"Task rejected by architect: {task} - {approval.rationale}"
                )
                return AgentResult(
                    status="rejected",
                    outcome=approval.outcome,
                    rationale=f"Architect rejected: {approval.rationale}",
                    approved=False,
                )

        # Execute the task
        return await agent.execute(task)

    async def handoff(
        self,
        from_agent: str,
        to_agent: str,
        context: dict,
    ) -> dict:
        """Transfer context between agents.

        Args:
            from_agent: Source agent type
            to_agent: Target agent type
            context: Context to transfer

        Returns:
            Handoff result
        """
        source = self.get_agent(from_agent)
        target = self.get_agent(to_agent)

        # Source agent summarizes relevant memories
        task_description = context.get("task", "")
        memories = await source.recall(task_description, limit=3)

        # Target agent receives handoff observation
        await target.remember(
            f"Handoff from @{from_agent}: {context}",
            memory_type="observation",
            importance=0.6,
            additional_context={
                "handoff_from": from_agent,
                "memories_transferred": len(memories),
            },
        )

        logger.info(f"Handoff: @{from_agent} -> @{to_agent}, {len(memories)} memories")

        return {
            "status": "transferred",
            "from": from_agent,
            "to": to_agent,
            "memories_shared": len(memories),
        }

    async def broadcast(
        self,
        message: str,
        importance: float = 0.5,
        exclude: Optional[list[str]] = None,
    ) -> dict:
        """Broadcast a message to all agents.

        Args:
            message: Message to broadcast
            importance: Memory importance
            exclude: Agent types to exclude

        Returns:
            Broadcast result
        """
        exclude = exclude or []
        results = {}

        for agent_type in AGENT_REGISTRY:
            if agent_type in exclude:
                continue

            agent = self.get_agent(agent_type)
            await agent.remember(
                f"Broadcast: {message}",
                memory_type="observation",
                importance=importance,
            )
            results[agent_type] = "received"

        return {"status": "broadcast", "agents": results}

    async def get_status(self) -> dict:
        """Get status from all agents.

        Returns:
            Dict with status from each agent
        """
        status = {}

        # Architect status (budget)
        architect = self.get_agent("architect")
        status["architect"] = await architect.get_status_report()

        # Ingestion status (sync state)
        ingestion = self.get_agent("ingestion")
        status["ingestion"] = await ingestion.get_sync_status()

        # DBAdmin status (database stats)
        try:
            dbadmin = self.get_agent("dbadmin")
            status["dbadmin"] = await dbadmin.get_database_stats()
        except Exception as e:
            status["dbadmin"] = {"error": str(e)}

        return status

    async def start_coordinated_session(
        self,
        goal: str,
        lead_agent: str = "architect",
        supporting_agents: Optional[list[str]] = None,
    ) -> UUID:
        """Start a coordinated multi-agent session.

        Args:
            goal: Session goal
            lead_agent: Primary agent for the session
            supporting_agents: Additional agents to involve

        Returns:
            Session UUID
        """
        supporting_agents = supporting_agents or []

        # Start session on lead agent
        lead = self.get_agent(lead_agent)
        session_id = await lead.start_session(goal)

        # Set context on supporting agents
        for agent_type in supporting_agents:
            if agent_type != lead_agent:
                agent = self.get_agent(agent_type)
                context = AgentContext.create(
                    goal=f"Supporting @{lead_agent}: {goal}",
                )
                context.session_id = session_id
                agent.set_context(context)

        return session_id

    async def end_coordinated_session(
        self,
        session_id: UUID,
        outcome: Optional[dict] = None,
    ) -> None:
        """End a coordinated multi-agent session.

        Args:
            session_id: Session UUID
            outcome: Optional outcome data
        """
        for agent_type, agent in self._agents.items():
            if agent.context and agent.context.session_id == session_id:
                await agent.end_session(outcome)


async def create_orchestrator(session: AsyncSession) -> AgentOrchestrator:
    """Factory function to create an orchestrator.

    Args:
        session: Database session

    Returns:
        Configured AgentOrchestrator
    """
    from iety.agents.memory.store import MemoryStore
    from iety.processing.embeddings import EmbeddingService
    from iety.cost.tracker import CostTracker

    memory_store = MemoryStore(session)
    cost_tracker = CostTracker(session)

    # Create embedding service (may fail if no API key)
    try:
        embedding_service = EmbeddingService(session, cost_tracker)
    except Exception:
        embedding_service = None
        logger.warning("Embedding service unavailable - agent memory search disabled")

    return AgentOrchestrator(
        session=session,
        memory_store=memory_store,
        embedding_service=embedding_service,
        cost_tracker=cost_tracker,
    )
