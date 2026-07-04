from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobRead(BaseModel):
    """What the API returns for a job. Deliberately a separate class from the
    ORM model: we choose exactly what leaves the API (no internal field can
    leak by accident), and FastAPI uses it to document and validate responses.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    title: str
    company: str
    url: str
    location: str | None
    remote: bool
    tags: list[str] | None
    posted_at: datetime | None
    created_at: datetime


class JobCreate(BaseModel):
    """A job listing in OUR normalized format, whatever the source.

    Every scraper must translate its source's raw JSON into this shape;
    the rest of the app never deals with source-specific field names.
    """

    source: str
    external_id: str
    title: str
    company: str
    url: str
    location: str | None = None
    remote: bool = False
    tags: list[str] = []
    posted_at: datetime | None = None
