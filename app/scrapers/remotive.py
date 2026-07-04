from datetime import UTC, datetime

import httpx

from app.schemas.job import JobCreate
from app.scrapers.base import TIMEOUT_SECONDS, USER_AGENT

API_URL = "https://remotive.com/api/remote-jobs"


class RemotiveScraper:
    name = "remotive"

    def fetch(self) -> list[JobCreate]:
        response = httpx.get(
            API_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()

        jobs: list[JobCreate] = []
        for item in payload["jobs"]:
            # publication_date is ISO format without timezone; Remotive
            # documents it as UTC, so we attach UTC explicitly.
            posted_at = None
            if item.get("publication_date"):
                posted_at = datetime.fromisoformat(item["publication_date"]).replace(tzinfo=UTC)
            jobs.append(
                JobCreate(
                    source=self.name,
                    external_id=str(item["id"]),
                    title=item["title"],
                    company=item["company_name"],
                    url=item["url"],
                    location=item.get("candidate_required_location") or None,
                    remote=True,  # Remotive only lists remote jobs
                    tags=item.get("tags") or [],
                    posted_at=posted_at,
                )
            )
        return jobs
