"""Check UUID format in database."""
import asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from signup.models import Tenant
from signup._core import get_settings


async def check_uuid_format():
    """Check how UUIDs are stored in the database."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)

    async with async_session() as session:
        # Check tenants table structure
        print("=== Tenants Table Structure ===")
        result = await session.execute(
            text("DESCRIBE tenants")
        )
        for row in result:
            print(f"{row[0]:<20} {row[1]:<30} {str(row[2]):<10}")

        print("\n=== Tenant Records (Raw SQL) ===")
        result = await session.execute(
            text("SELECT id, name, is_active FROM tenants")
        )
        for row in result:
            print(f"ID: {row[0]} (type: {type(row[0]).__name__})")
            print(f"  Name: {row[1]}, Active: {row[2]}")

        print("\n=== Tenant Records (ORM) ===")
        result = await session.execute(select(Tenant))
        tenants = result.scalars().all()
        for tenant in tenants:
            print(f"ID: {tenant.id} (type: {type(tenant.id).__name__})")
            print(f"  Name: {tenant.name}, Active: {tenant.is_active}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_uuid_format())
