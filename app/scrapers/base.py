from typing import Protocol

from app.schemas.job import JobCreate

# Shared HTTP settings for all scrapers. Some APIs (RemoteOK) reject
# requests without a User-Agent identifying the caller.
USER_AGENT = "job-application-tracker (personal learning project)"
TIMEOUT_SECONDS = 20.0


class JobSource(Protocol):
    """Contract every scraper must fulfill: a name and a fetch() method
    returning jobs in our normalized JobCreate format."""

    name: str

    def fetch(self) -> list[JobCreate]: ...
