"""Seed default tenant into the database."""
import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from signup.models import Base, Tenant


async def seed_default_tenant():
    """Create a default tenant."""
    from signup._core import get_settings

    settings = get_settings()

    # Create engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if default tenant exists
        from sqlalchemy import select
        result = await session.execute(
            select(Tenant).where(Tenant.name == "Default")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("[OK] Default tenant already exists")
            return

        # Create default tenant
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Default",
            domain="localhost",
            is_active=True,
        )
        session.add(tenant)
        await session.commit()

        print(f"[OK] Created default tenant: {tenant.id}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_default_tenant())
