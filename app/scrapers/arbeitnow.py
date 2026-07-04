from datetime import UTC, datetime

import httpx

from app.schemas.job import JobCreate
from app.scrapers.base import TIMEOUT_SECONDS, USER_AGENT

API_URL = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowScraper:
    name = "arbeitnow"

    def fetch(self) -> list[JobCreate]:
        response = httpx.get(
            API_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()

        jobs: list[JobCreate] = []
        for item in payload["data"]:
            jobs.append(
                JobCreate(
                    source=self.name,
                    external_id=item["slug"],
                    title=item["title"],
                    company=item["company_name"],
                    url=item["url"],
                    location=item.get("location") or None,
                    remote=item.get("remote", False),
                    tags=item.get("tags") or [],
                    posted_at=datetime.fromtimestamp(item["created_at"], tz=UTC)
                    if item.get("created_at")
                    else None,
                )
            )
        return jobs
