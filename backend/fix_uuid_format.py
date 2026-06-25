"""Fix malformed UUIDs in the database."""
import asyncio
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from signup.models import Tenant
from signup._core import get_settings


async def fix_uuid_format():
    """Fix UUIDs that are missing hyphens."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)

    async with async_session() as session:
        # Find UUIDs without hyphens (32 chars)
        print("=== Finding malformed UUIDs ===")
        result = await session.execute(
            select(Tenant)
        )
        tenants = result.scalars().all()

        fixed_count = 0
        for tenant in tenants:
            uuid_str = str(tenant.id)
            print(f"Tenant: {tenant.name}")
            print(f"  Current ID: {uuid_str} (len: {len(uuid_str)})")

            # Check if UUID is malformed (missing hyphens)
            if len(uuid_str) == 32 and '-' not in uuid_str:
                # Add hyphens in correct positions: 8-4-4-4-12
                fixed_uuid = f"{uuid_str[0:8]}-{uuid_str[8:12]}-{uuid_str[12:16]}-{uuid_str[16:20]}-{uuid_str[20:32]}"
                print(f"  Fixing to: {fixed_uuid}")

                # Update in database
                await session.execute(
                    text(f"""
                        UPDATE tenants
                        SET id = :new_id
                        WHERE id = :old_id
                    """),
                    {"new_id": fixed_uuid, "old_id": uuid_str}
                )
                fixed_count += 1
            else:
                print(f"  OK (already formatted)")

        if fixed_count > 0:
            await session.commit()
            print(f"\n[OK] Fixed {fixed_count} malformed UUID(s)")
        else:
            print(f"\n[OK] All UUIDs are properly formatted")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(fix_uuid_format())
