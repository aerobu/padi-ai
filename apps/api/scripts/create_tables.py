"""
Create database tables from SQLAlchemy models.
Run this once to initialize the database before running migrations.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from src.models.base import Base
from src.core.config import get_settings


async def create_tables():
    """Create all tables in the database."""
    settings = get_settings()

    # Use sync engine for table creation
    from sqlalchemy import create_engine
    sync_url = settings.DATABASE_URL.replace("asyncpg://", "postgresql://").replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(sync_url, echo=False)

    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("✓ Tables created successfully")

    # Verify tables exist
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))  # type: ignore
        tables = [row[0] for row in conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))]
        print(f"✓ Created {len(tables)} tables: {', '.join(tables)}")

    await engine.dispose()


if __name__ == "__main__":
    # For sync engine
    from sqlalchemy import create_engine
    import asyncio

    settings = get_settings()
    sync_url = settings.DATABASE_URL.replace("asyncpg://", "postgresql://").replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(sync_url, echo=False)

    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("✓ Tables created successfully")

    with engine.connect() as conn:
        tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")).fetchall()
        print(f"✓ Created {len(tables)} tables")
