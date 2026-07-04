import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.ingest import scrape_all

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def scheduled_scrape() -> None:
    """The job APScheduler runs on a timer: scrape, store, notify."""
    logger.info("scheduled scrape starting")
    with SessionLocal() as db:
        results = scrape_all(db)
        db.commit()
    logger.info("scheduled scrape done: %s", results)


def start_scheduler() -> None:
    scheduler.add_job(
        scheduled_scrape,
        trigger="interval",
        hours=settings.scrape_interval_hours,
        id="scrape_jobs",
        # If the machine slept past a run, do one catch-up run instead of
        # stacking every missed occurrence.
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("scheduler started: scraping every %dh", settings.scrape_interval_hours)


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
