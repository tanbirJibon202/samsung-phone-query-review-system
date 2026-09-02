from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.models import Base

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create tables and apply the small, idempotent schema upgrades."""
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE specifications ADD COLUMN IF NOT EXISTS battery_active_use_hours DOUBLE PRECISION")
            )
            connection.execute(
                text("ALTER TABLE specifications ADD COLUMN IF NOT EXISTS battery_endurance_hours INTEGER")
            )
            connection.execute(
                text("ALTER TABLE specifications ADD COLUMN IF NOT EXISTS price_summary TEXT")
            )


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
