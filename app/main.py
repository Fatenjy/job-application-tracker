from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routers import applications, jobs
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Runs at startup / shutdown of the API: the scheduler lives and dies
    # with the web process.
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Job Application Tracker",
    description="Tracks job listings from public APIs and notifies new matches.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(jobs.router)
app.include_router(applications.router)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """Visitors landing on the bare domain go straight to the API docs."""
    return RedirectResponse("/docs")


@app.get("/health", tags=["monitoring"])
def health(db: Session = Depends(get_db)) -> dict:
    """Liveness check: proves the API is up AND can reach the database."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
