import asyncio
import json
from pathlib import Path
from app.SQLite.db import async_session, Spot, Booking

SPOTS = json.loads(Path(__file__).parent.joinpath("seed_spots.json").read_text(encoding="utf-8"))
BOOKINGS = json.loads(Path(__file__).parent.joinpath("seed_bookings.json").read_text(encoding="utf-8"))


async def seed():
    async with async_session() as session:
        for data in SPOTS:
            session.add(Spot(**data))
        await session.commit()
        print(f"Seeded {len(SPOTS)} spots.")

    async with async_session() as session:
        for data in BOOKINGS:
            session.add(Booking(**data))
        await session.commit()
        print(f"Seeded {len(BOOKINGS)} bookings.")

async def reset_and_seed():
    from app.SQLite.db import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed()

if __name__ == "__main__":
    asyncio.run(reset_and_seed())
