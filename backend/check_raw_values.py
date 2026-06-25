"""Check raw database values."""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from signup._core import get_settings


async def check_raw():
    """Check raw values in database."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)

    async with async_session() as session:
        print("=== Raw tenant IDs ===")
        result = await session.execute(
            text("SELECT id, HEX(id), CHAR_LENGTH(id), name FROM tenants ORDER BY created_at")
        )
        for row in result:
            print(f"ID: {row[0]}")
            print(f"  HEX: {row[1]}")
            print(f"  LENGTH: {row[2]}")
            print(f"  NAME: {row[3]}")
            print()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_raw())
