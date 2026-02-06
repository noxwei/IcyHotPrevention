"""Unit tests for MemoryStore SQL injection prevention."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from iety.agents.memory.store import MemoryStore


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    session.execute = AsyncMock(return_value=mock_result)
    session.commit = AsyncMock()
    return session


@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service returning a fixed vector."""
    service = MagicMock()
    service.embed_query = AsyncMock(return_value=[0.1] * 1024)
    return service


class TestMemoryStoreSearch:
    """Tests that MemoryStore.search() uses parameterized queries."""

    @pytest.mark.asyncio
    async def test_search_with_memory_types_uses_parameterized_any(
        self, mock_session, mock_embedding_service
    ):
        """search() with memory_types should use ANY(:memory_types) param, not string interpolation."""
        store = MemoryStore(mock_session)

        await store.search(
            agent_type="architect",
            query="test query",
            embedding_service=mock_embedding_service,
            memory_types=["observation", "decision"],
        )

        # Get the SQL text and params from the execute call
        call_args = mock_session.execute.call_args
        sql_obj = call_args[0][0]
        params = call_args[0][1]

        sql_text = str(sql_obj.text)

        # SQL must use :memory_types placeholder, not interpolated values
        assert "ANY(:memory_types)" in sql_text
        assert "'observation'" not in sql_text
        assert "'decision'" not in sql_text

        # Values must be in the params dict
        assert params["memory_types"] == ["observation", "decision"]

    @pytest.mark.asyncio
    async def test_search_without_memory_types_omits_type_filter(
        self, mock_session, mock_embedding_service
    ):
        """search() without memory_types should not include type filter in SQL."""
        store = MemoryStore(mock_session)

        await store.search(
            agent_type="architect",
            query="test query",
            embedding_service=mock_embedding_service,
            memory_types=None,
        )

        call_args = mock_session.execute.call_args
        sql_obj = call_args[0][0]
        params = call_args[0][1]
        sql_text = str(sql_obj.text)

        assert "ANY(:memory_types)" not in sql_text
        assert "memory_types" not in params

    @pytest.mark.asyncio
    async def test_malicious_memory_types_stay_in_params(
        self, mock_session, mock_embedding_service
    ):
        """Malicious memory_types values must stay in params dict, never appear in SQL text."""
        store = MemoryStore(mock_session)
        malicious = ["'; DROP TABLE agent_memory; --"]

        await store.search(
            agent_type="architect",
            query="test query",
            embedding_service=mock_embedding_service,
            memory_types=malicious,
        )

        call_args = mock_session.execute.call_args
        sql_obj = call_args[0][0]
        params = call_args[0][1]

        sql_text = str(sql_obj.text)

        # Malicious string must NOT appear in SQL text
        assert "DROP TABLE" not in sql_text

        # It should only exist in the params dict
        assert params["memory_types"] == malicious
