"""Database async engine, session, and base for SQLAlchemy."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Async engine: use postgresql+asyncpg:// or sqlite+aiosqlite://
database_url = settings.database_url
if database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    database_url,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()


async def init_db() -> None:
    """Create schema (PostgreSQL) and all tables. Call once at startup."""
    from sqlalchemy import text

    from app import models  # noqa: F401  # register models

    async with engine.begin() as conn:
        if "postgresql" in database_url:
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS classification"))
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI: yield an async session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
