from datetime import datetime

from pydantic import BaseModel


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
