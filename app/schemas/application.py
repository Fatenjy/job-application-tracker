from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.application import ApplicationStatus
from app.schemas.job import JobRead


class ApplicationCreate(BaseModel):
    job_id: int
    status: ApplicationStatus = ApplicationStatus.SAVED
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    """All fields optional: a PATCH sends only what changes."""

    status: ApplicationStatus | None = None
    notes: str | None = None
    applied_at: datetime | None = None


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ApplicationStatus
    notes: str | None
    applied_at: datetime | None
    created_at: datetime
    updated_at: datetime
    job: JobRead  # the full listing comes embedded — no second request needed
