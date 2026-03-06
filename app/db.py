"""
app/db.py — SQLAlchemy / PostgreSQL database engine (Member 1 Work).
"""
import os
import time
import logging
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Float, Integer, String, create_engine, StaticPool
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

if os.getenv("TESTING") == "1":
    # Use SQLite for tests to avoid needing a live Postgres connection.
    # StaticPool is required for :memory: to persist across connections.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # Connection engine for PostgreSQL
    engine = create_engine(settings.DATABASE_URL)
    
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# ORM model — assignment log
# ---------------------------------------------------------------------------

class AssignmentLog(Base):
    """Persists every assignment result for audit / analytics."""

    __tablename__ = "assignment_log"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Who got what
    courier_id = Column(String(64), nullable=False, index=True)
    order_id = Column(String(64), nullable=False, index=True)

    # Why (reasoning fields)
    reason_distance_km = Column(Float, nullable=True)
    reason_duration_min = Column(Float, nullable=True)  # Time Factor
    solver_status = Column(String(32), nullable=True)
    solved_in_ms = Column(Float, nullable=True)

    # ML & SLA Fields (Member 1 Enhancement)
    order_priority = Column(Integer, nullable=True)
    order_deadline = Column(DateTime, nullable=True)


def create_tables() -> None:
    """
    Create all tables with a retry loop (Member 1 Resilience Upgrade).
    Ensures the app doesn't crash if the database is still warming up.
    """
    retries = 5
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception as e:
            retries -= 1
            logging.error(f"Database not ready. Retrying in 5s... ({retries} left)")
            time.sleep(5)
    
    # Final attempt to crash with a clear error if retries failed
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
