from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

app = FastAPI(
    title="Job Application Tracker",
    description="Tracks job listings from public APIs and notifies new matches.",
    version="0.1.0",
)


@app.get("/health", tags=["monitoring"])
def health(db: Session = Depends(get_db)) -> dict:
    """Liveness check: proves the API is up AND can reach the database."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
