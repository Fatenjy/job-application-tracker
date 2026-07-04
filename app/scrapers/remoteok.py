from datetime import UTC, datetime

import httpx

from app.schemas.job import JobCreate
from app.scrapers.base import TIMEOUT_SECONDS, USER_AGENT

API_URL = "https://remoteok.com/api"


class RemoteOKScraper:
    name = "remoteok"

    def fetch(self) -> list[JobCreate]:
        response = httpx.get(
            API_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        response.raise_for_status()
        payload = response.json()

        jobs: list[JobCreate] = []
        for item in payload:
            # The first element is a legal notice, not a job listing.
            if "legal" in item or not item.get("id"):
                continue
            jobs.append(
                JobCreate(
                    source=self.name,
                    external_id=str(item["id"]),
                    title=item["position"],
                    company=item["company"],
                    url=item["url"],
                    location=item.get("location") or None,
                    remote=True,  # every listing on RemoteOK is remote by definition
                    tags=item.get("tags") or [],
                    posted_at=datetime.fromtimestamp(item["epoch"], tz=UTC)
                    if item.get("epoch")
                    else None,
                )
            )
        return jobs
