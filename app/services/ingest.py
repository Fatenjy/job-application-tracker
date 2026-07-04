import logging

import truststore
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate
from app.scrapers.arbeitnow import ArbeitnowScraper
from app.scrapers.base import JobSource
from app.scrapers.remoteok import RemoteOKScraper
from app.scrapers.remotive import RemotiveScraper
from app.services.notifier import notify_new_jobs

logger = logging.getLogger(__name__)

# Use the operating system's certificate store for TLS verification instead of
# Python's bundled list. Required when HTTPS is inspected by a local antivirus
# or corporate proxy (their root certificate lives in the OS store only).
truststore.inject_into_ssl()

SCRAPERS: list[JobSource] = [RemoteOKScraper(), ArbeitnowScraper(), RemotiveScraper()]


def ingest_jobs(db: Session, jobs: list[JobCreate]) -> list[int]:
    """Insert scraped jobs, silently skipping ones we already have.

    Deduplication happens in PostgreSQL itself via the unique
    (source, external_id) constraint: ON CONFLICT DO NOTHING makes the
    operation idempotent — running the scraper twice changes nothing.
    Returns the ids of the genuinely new rows.
    """
    if not jobs:
        return []
    stmt = (
        insert(Job)
        .values([job.model_dump() for job in jobs])
        .on_conflict_do_nothing(constraint="uq_jobs_source_external_id")
        # RETURNING gives back only the rows actually inserted (skipped
        # duplicates are excluded): exactly the new jobs, nothing else.
        .returning(Job.id)
    )
    return list(db.scalars(stmt))


def scrape_all(db: Session) -> dict[str, int | None]:
    """Run every scraper, ingest results, notify about matching new jobs.

    One failing source must not prevent the others from being collected.
    None marks a failed source (never a number: counts and error signals
    must not share a type)."""
    new_by_source: dict[str, int | None] = {}
    all_new_ids: list[int] = []
    for scraper in SCRAPERS:
        try:
            jobs = scraper.fetch()
        except Exception:
            logger.exception("scraper %s failed, skipping", scraper.name)
            new_by_source[scraper.name] = None
            continue
        new_ids = ingest_jobs(db, jobs)
        new_by_source[scraper.name] = len(new_ids)
        all_new_ids.extend(new_ids)

    if all_new_ids:
        new_jobs = list(db.scalars(select(Job).where(Job.id.in_(all_new_ids))))
        notified = notify_new_jobs(new_jobs)
        if notified:
            logger.info("notified %d matching new jobs via telegram", notified)
    return new_by_source


if __name__ == "__main__":
    # Manual run: python -m app.services.ingest
    logging.basicConfig(level=logging.INFO)
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        results = scrape_all(session)
        session.commit()
    for source, count in results.items():
        status = "ERREUR (voir logs)" if count is None else f"{count} nouvelles offres"
        print(f"{source}: {status}")
