from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Application, Job
from app.schemas.application import ApplicationCreate, ApplicationRead, ApplicationUpdate

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationRead, status_code=201)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)) -> Application:
    """Start tracking an application for a job listing."""
    if db.get(Job, payload.job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")
    existing = db.scalar(select(Application).where(Application.job_id == payload.job_id))
    if existing is not None:
        # 409 Conflict: the request is valid but collides with current state.
        raise HTTPException(status_code=409, detail="Application already exists for this job")
    application = Application(**payload.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("", response_model=list[ApplicationRead])
def list_applications(db: Session = Depends(get_db)) -> list[Application]:
    # joinedload fetches each application WITH its job in a single SQL query,
    # instead of one extra query per row (the classic "N+1" performance trap).
    stmt = (
        select(Application)
        .options(joinedload(Application.job))
        .order_by(Application.updated_at.desc())
    )
    return list(db.scalars(stmt))


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: int, payload: ApplicationUpdate, db: Session = Depends(get_db)
) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    # exclude_unset: only touch the fields the client actually sent.
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(application, field, value)
    db.commit()
    db.refresh(application)
    return application


@router.delete("/{application_id}", status_code=204)
def delete_application(application_id: int, db: Session = Depends(get_db)) -> Response:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(application)
    db.commit()
    return Response(status_code=204)
