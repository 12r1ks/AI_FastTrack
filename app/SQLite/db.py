from collections.abc import AsyncGenerator
import uuid

from sqlalchemy import Column, Float, Float, Integer, PrimaryKeyConstraint, String, DateTime, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, declarative_base, relationship

DATABASE_URL = "sqlite+aiosqlite:///./app/db/Dynamic_SQLite_DB.db"

class Base(DeclarativeBase):
    pass

class Spot(Base): 

    __tablename__ = "spots" 

    __table_args__ = (PrimaryKeyConstraint("id", "location"),)                                                                                                      
    id = Column(String,  nullable=False)    # e.g. A1, B1, T3         
    location = Column(String,  nullable=False)      # central | east         
    type = Column(String,  nullable=False)      # standard | premium | truck                                                                             
    hourly_rate = Column(Float,   nullable=False)                               
    daily_rate = Column(Float,   nullable=False)                               
    bookings = relationship("Booking", back_populates="spot")     


class Booking(Base):
    __tablename__ = "BOOKINGS"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    spot_id      = Column(String,  ForeignKey("spots.id"), nullable=False)
    location     = Column(String,  nullable=False)     # central | east
    booking_type = Column(String,  nullable=False)     # reservation | block
    name         = Column(String,  nullable=False)     # client name or CityPark
    car_number   = Column(String,  nullable=True)
    reason       = Column(String,  nullable=True)
    start_dt     = Column(String,  nullable=False)     # YYYY-MM-DD HH:MM
    end_dt       = Column(String,  nullable=False)     # YYYY-MM-DD HH:MM
    status       = Column(String,  nullable=False)     # approved | cancelled
    created_at   = Column(String,  nullable=False)     # YYYY-MM-DD HH:MM

    spot = relationship("Spot", back_populates="bookings")



engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


if __name__ == "__main__":
    import asyncio
    asyncio.run(create_db_and_tables())
