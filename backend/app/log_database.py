"""Dedicated database connection and metadata for durable logging tables."""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings
import logging

logger = logging.getLogger(__name__)

log_engine = create_async_engine(
    settings.LOG_DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

LogSessionLocal = async_sessionmaker(
    log_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

LogBase = declarative_base()


async def get_log_db() -> AsyncSession:
    """Yield an async session for the dedicated logging database."""
    async with LogSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_log_db() -> None:
    """Create durable logging tables in the dedicated logging database."""
    async with log_engine.begin() as conn:
        logger.info("Creating logging database tables...")
        await conn.run_sync(LogBase.metadata.create_all)
        logger.info("Logging database tables created successfully")


async def close_log_db() -> None:
    """Close connections for the dedicated logging database."""
    logger.info("Closing logging database connections...")
    await log_engine.dispose()
    logger.info("Logging database connections closed")
