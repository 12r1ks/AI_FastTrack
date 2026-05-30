import asyncio
from sqlalchemy import select, and_
from app.SQLite.db import async_session, Spot, Booking
from typing_extensions import Literal, Annotated

async def query_booked_spots(
        location: Annotated[Literal["east","central"],"Location of the parking lot"],
        start_time: str,
        end_time: str,
        parking_spot_type: Annotated[Literal["A", "B", "T"], "Type of parking spot"]
        ):
    
    async with async_session() as session:
        spots = await session.execute(
                  select(Booking)
                  .where(
                      and_(
                          Booking.start_dt < end_time,
                          Booking.end_dt > start_time,
                          Booking.location == location,
                          Booking.spot_id.like(f"{parking_spot_type}%"),
                          Booking.status == "approved"
                      )
                  )
        )
        
        spots = spots.scalars().all()
        booked = [s.spot_id for s in spots]
        return booked

async def query_available_spots(
        location: Annotated[Literal["east","central"],"Location of the parking lot"],
        start_time: str,
        end_time: str,
        parking_spot_type: Annotated[Literal["A", "B", "T"], "Type of parking spot"]
        ):
    async with async_session() as session:
        spots = await session.execute(
                  select(Spot).where(
                      Spot.id.like(f"{parking_spot_type}%"),
                      Spot.location == location
                  )
                  )
        booked = await query_booked_spots(location, start_time, end_time, parking_spot_type)

        spots = spots.scalars().all()
        available = [s.id for s in spots if s.id not in booked]
        return available


if __name__ == "__main__":
    start = "2026-06-20 10:00"
    end = "2026-06-21 12:00"
    b = asyncio.run(query_booked_spots("east", start, end, "A"))
    s = asyncio.run(query_available_spots("east", start, end, "A"))
    print(s,b)