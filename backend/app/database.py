"""Database connection and session management."""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings

logger = logging.getLogger(__name__)

# Real engines (service-owned)
profile_engine = create_async_engine(
    settings.PROFILE_DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

ai_engine = create_async_engine(
    settings.AI_DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Real session factories (service-owned)
ProfileAsyncSessionLocal = async_sessionmaker(
    profile_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

AIAsyncSessionLocal = async_sessionmaker(
    ai_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Real declarative bases (service-owned)
ProfileBase = declarative_base()
AIBase = declarative_base()

# Compatibility aliases (temporary)
engine = profile_engine
AsyncSessionLocal = ProfileAsyncSessionLocal
Base = ProfileBase


async def get_profile_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for profile database sessions."""
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
    """Dependency for AI database sessions."""
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
    logger.info("Creating profile database tables...")
    async with profile_engine.begin() as conn:
        await conn.run_sync(ProfileBase.metadata.create_all)

    logger.info("Creating AI database tables...")
    async with ai_engine.begin() as conn:
        await conn.run_sync(AIBase.metadata.create_all)

    logger.info("Database tables created successfully")


async def close_db() -> None:
    """Close database connections."""
    logger.info("Closing database connections...")
    await profile_engine.dispose()
    await ai_engine.dispose()
    logger.info("Database connections closed")
