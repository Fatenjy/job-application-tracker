import logging

import truststore
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate
from app.scrapers.arbeitnow import ArbeitnowScraper
from app.scrapers.base import JobSource
from app.scrapers.remoteok import RemoteOKScraper
from app.scrapers.remotive import RemotiveScraper

logger = logging.getLogger(__name__)

# Use the operating system's certificate store for TLS verification instead of
# Python's bundled list. Required when HTTPS is inspected by a local antivirus
# or corporate proxy (their root certificate lives in the OS store only).
truststore.inject_into_ssl()

SCRAPERS: list[JobSource] = [RemoteOKScraper(), ArbeitnowScraper(), RemotiveScraper()]


def ingest_jobs(db: Session, jobs: list[JobCreate]) -> int:
    """Insert scraped jobs, silently skipping ones we already have.

    Deduplication happens in PostgreSQL itself via the unique
    (source, external_id) constraint: ON CONFLICT DO NOTHING makes the
    operation idempotent — running the scraper twice changes nothing.
    Returns the number of genuinely new rows.
    """
    if not jobs:
        return 0
    stmt = (
        insert(Job)
        .values([job.model_dump() for job in jobs])
        .on_conflict_do_nothing(constraint="uq_jobs_source_external_id")
        # RETURNING gives back only the rows actually inserted (skipped
        # duplicates are excluded), so we get an exact count of new jobs.
        .returning(Job.id)
    )
    result = db.execute(stmt)
    return len(result.fetchall())


def scrape_all(db: Session) -> dict[str, int | None]:
    """Run every scraper and ingest results. One failing source must not
    prevent the others from being collected. None marks a failed source
    (never a number: counts and error signals must not share a type)."""
    new_by_source: dict[str, int | None] = {}
    for scraper in SCRAPERS:
        try:
            jobs = scraper.fetch()
        except Exception:
            logger.exception("scraper %s failed, skipping", scraper.name)
            new_by_source[scraper.name] = None
            continue
        new_by_source[scraper.name] = ingest_jobs(db, jobs)
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
