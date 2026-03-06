"""
app/db.py — SQLAlchemy / PostgreSQL database engine (Member 1 Work).
"""
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Float, Integer, String, create_engine
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

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
    solver_status = Column(String(32), nullable=True)
    solved_in_ms = Column(Float, nullable=True)

    # ML & SLA Fields (Member 1 Enhancement)
    order_priority = Column(Integer, nullable=True)
    order_deadline = Column(DateTime, nullable=True)


def create_tables() -> None:
    """Create all tables. Called on app startup."""
    # In a real project with PostGIS, you'd use migrations (Alembic).
    # For a prototype, this ensures Member 1's tables exist.
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
