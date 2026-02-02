"""Async SQLAlchemy database engine configuration."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from iety.config import get_settings

# Global engine instance
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine(use_pool: bool = True) -> AsyncEngine:
    """Get or create the async database engine.

    Args:
        use_pool: Whether to use connection pooling. Set False for tests.

    Returns:
        AsyncEngine instance
    """
    global _engine

    if _engine is not None:
        return _engine

    settings = get_settings()

    pool_kwargs = {}
    if use_pool:
        pool_kwargs = {
            "pool_size": settings.database.pool_size,
            "max_overflow": settings.database.max_overflow,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }
    else:
        pool_kwargs = {"poolclass": NullPool}

    _engine = create_async_engine(
        settings.database.async_url,
        echo=settings.debug,
        **pool_kwargs,
    )

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the session factory."""
    global _session_factory

    if _session_factory is not None:
        return _session_factory

    engine = get_engine()
    _session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields database sessions.

    Usage:
        async for session in get_session():
            await session.execute(...)
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions.

    Usage:
        async with session_context() as session:
            await session.execute(...)
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_engine() -> None:
    """Close the database engine and release connections."""
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


def reset_engine() -> None:
    """Reset the engine for testing purposes."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
