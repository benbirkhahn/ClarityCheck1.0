
import asyncio
from backend.core.database import init_db
from backend.core.models import * # Import models to register them
from sqlmodel import SQLModel
from backend.core.database import engine

async def recreate_tables():
    print("Dropping and recreating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    print("Database schema updated successfully!")

if __name__ == "__main__":
    asyncio.run(recreate_tables())
