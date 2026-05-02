from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.config import settings

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

# Apply connection pool limits only for PostgreSQL (not SQLite)
if "postgresql" in DATABASE_URL:
    engine = create_async_engine(
        DATABASE_URL, 
        echo=settings.DEBUG, 
        future=True,
        pool_size=5,
        max_overflow=0
    )
else:
    engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG, future=True)

if "postgresql" in SYNC_DATABASE_URL:
    sync_engine = create_engine(
        SYNC_DATABASE_URL, 
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=0
    )
else:
    sync_engine = create_engine(SYNC_DATABASE_URL, echo=settings.DEBUG)

async def init_db():
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

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
