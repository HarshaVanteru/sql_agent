"""Check users table schema."""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from signup._core import get_settings


async def check_schema():
    """Check users table schema."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)

    async with async_session() as session:
        print("=== Users Table Structure ===")
        result = await session.execute(
            text("DESCRIBE users")
        )
        for row in result:
            print(f"{row[0]:<25} {row[1]:<30} {str(row[2]):<10}")

        print("\n=== Foreign Key Constraints ===")
        result = await session.execute(
            text("""
                SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_NAME = 'users' AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
        )
        for row in result:
            print(f"Constraint: {row[0]}")
            print(f"  Column: {row[1]} -> {row[2]}.{row[3]}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_schema())
