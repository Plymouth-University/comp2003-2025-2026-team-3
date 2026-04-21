"""Database connection and session management."""

import logging
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings

logger = logging.getLogger(__name__)

# Core engine owns profile/auth/tenant data and AI ticket-state data.
core_engine = create_async_engine(
    settings.CORE_DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factories keep service-facing names for compatibility while sharing
# one physical database so profile foreign keys can protect AI ticket state.
CoreAsyncSessionLocal = async_sessionmaker(
    core_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
ProfileAsyncSessionLocal = CoreAsyncSessionLocal
AIAsyncSessionLocal = CoreAsyncSessionLocal

# Core declarative base. Compatibility aliases preserve existing imports.
CoreBase = declarative_base()
ProfileBase = CoreBase
AIBase = CoreBase

# Compatibility aliases (temporary)
engine = core_engine
AsyncSessionLocal = ProfileAsyncSessionLocal
Base = CoreBase


async def get_profile_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for profile/core database sessions."""
    async with ProfileAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_ai_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for AI ticket-state sessions in the core database."""
    async with AIAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Backward-compatible dependency alias (temporary)
get_db = get_profile_db


async def init_db() -> None:
    """Initialize database tables (development only)."""
    logger.info("Creating core database tables...")
    async with core_engine.begin() as conn:
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS "AITicketOps"'))
        await conn.run_sync(CoreBase.metadata.create_all)

    logger.info("Database tables created successfully")


async def close_db() -> None:
    """Close database connections."""
    logger.info("Closing database connections...")
    await core_engine.dispose()
    logger.info("Database connections closed")
