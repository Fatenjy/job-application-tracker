from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Job
from app.schemas.job import JobRead

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobRead])
def list_jobs(
    db: Session = Depends(get_db),
    q: str | None = Query(None, description="Recherche dans le titre ou l'entreprise"),
    tag: str | None = Query(None, description="Filtre par tag exact (ex. python)"),
    remote: bool | None = Query(None, description="Uniquement les offres remote (ou non)"),
    source: str | None = Query(None, description="remoteok ou arbeitnow"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[Job]:
    """List job offers, newest first, with optional filters."""
    stmt = select(Job).order_by(Job.posted_at.desc().nulls_last(), Job.id.desc())
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(Job.title.ilike(pattern), Job.company.ilike(pattern)))
    if tag:
        # JSONB containment: does the tags array contain this value?
        stmt = stmt.where(Job.tags.contains([tag]))
    if remote is not None:
        stmt = stmt.where(Job.remote == remote)
    if source:
        stmt = stmt.where(Job.source == source)
    return list(db.scalars(stmt.limit(limit).offset(offset)))


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
