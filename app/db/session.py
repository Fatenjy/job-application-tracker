from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models — SQLAlchemy collects their table
    definitions in Base.metadata (used later by Alembic migrations)."""


engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI dependency: opens a DB session for one request, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
