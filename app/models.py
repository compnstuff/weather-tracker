from sqlalchemy import Column, Integer, Float, String, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime, timezone

DATABASE_URL = "sqlite:///./weather.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class WeatherReading(Base):
    __tablename__ = "weather_readings"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    country = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    temp_c = Column(Float)
    feels_like_c = Column(Float)
    humidity = Column(Integer)
    pressure = Column(Integer)
    wind_speed = Column(Float)
    wind_deg = Column(Integer)
    description = Column(String)
    icon = Column(String)
    visibility = Column(Integer, nullable=True)
    clouds = Column(Integer)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
