from typing import AsyncGenerator
from contextlib import asynccontextmanager
import logging

from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.config import settings

logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

if "asyncpg" in DATABASE_URL:
    SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg2")
elif DATABASE_URL.startswith("sqlite+aiosqlite://"):
    SYNC_DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://", 1)
else:
    SYNC_DATABASE_URL = DATABASE_URL

def _create_engines(async_url: str, sync_url: str):
    """Create the async and sync SQLAlchemy engines for the active database."""
    if "postgresql" in async_url:
        async_engine = create_async_engine(
            async_url,
            echo=settings.DEBUG,
            future=True,
            pool_size=5,
            max_overflow=0,
        )
    else:
        async_engine = create_async_engine(async_url, echo=settings.DEBUG, future=True)

    if "postgresql" in sync_url:
        sync_db_engine = create_engine(
            sync_url,
            echo=settings.DEBUG,
            pool_size=5,
            max_overflow=0,
        )
    else:
        sync_db_engine = create_engine(sync_url, echo=settings.DEBUG)

    return async_engine, sync_db_engine


engine, sync_engine = _create_engines(DATABASE_URL, SYNC_DATABASE_URL)


def _switch_to_sqlite_fallback():
    """Fallback to a local SQLite database if the configured DB is unavailable."""
    global DATABASE_URL, SYNC_DATABASE_URL, engine, sync_engine

    DATABASE_URL = "sqlite+aiosqlite:///./clarity.db"
    SYNC_DATABASE_URL = "sqlite:///./clarity.db"
    engine, sync_engine = _create_engines(DATABASE_URL, SYNC_DATABASE_URL)
    logger.warning("Falling back to local SQLite database at ./clarity.db")

async def init_db():
    try:
        async with engine.begin() as conn:
            # await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)

            # Migrate: add is_admin column if it doesn't exist
            try:
                from sqlalchemy import text
                await conn.execute(text(
                    "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"
                ))
            except Exception:
                # Column already exists — safe to ignore
                pass
    except Exception as exc:
        if "sqlite" in DATABASE_URL:
            raise

        logger.exception("Primary database failed during startup: %s", exc)
        _switch_to_sqlite_fallback()

        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
