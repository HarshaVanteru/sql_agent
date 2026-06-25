"""Reset database and create fresh default tenant."""
import asyncio
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from signup.models import Base, Tenant
from signup._core import get_settings


async def reset_and_seed():
    """Delete all data and create fresh default tenant."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)

    async with async_session() as session:
        # Delete all users first (foreign key constraint)
        print("Deleting users...")
        await session.execute(text("DELETE FROM users"))

        # Delete all tenants
        print("Deleting tenants...")
        await session.execute(text("DELETE FROM tenants"))

        await session.commit()

    # Create fresh default tenant
    async with async_session() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Default",
            domain="localhost",
            is_active=True,
        )
        session.add(tenant)
        await session.commit()
        print(f"[OK] Created fresh default tenant: {tenant.id}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_and_seed())
