"""Ingestion tests: the deduplication contract is the heart of the pipeline —
running the same scrape twice must never create duplicates."""

from app.models import Job
from app.schemas.job import JobCreate
from app.services.ingest import ingest_jobs
from app.services.notifier import job_matches_keywords


def make_payload(external_id: str, title: str = "Python Dev") -> JobCreate:
    return JobCreate(
        source="test",
        external_id=external_id,
        title=title,
        company="ACME",
        url=f"https://example.com/{external_id}",
    )


def test_ingest_inserts_and_returns_new_ids(db):
    new_ids = ingest_jobs(db, [make_payload("a"), make_payload("b")])
    db.commit()
    assert len(new_ids) == 2


def test_ingest_is_idempotent(db):
    first = ingest_jobs(db, [make_payload("a"), make_payload("b")])
    db.commit()
    # same batch again, plus one genuinely new job
    second = ingest_jobs(db, [make_payload("a"), make_payload("b"), make_payload("c")])
    db.commit()

    assert len(first) == 2
    assert len(second) == 1  # only "c" is new
    assert db.query(Job).count() == 3  # no duplicates in the table


def test_keyword_matching():
    job = Job(
        source="test",
        external_id="x",
        title="Senior Backend Engineer",
        company="ACME",
        url="https://example.com/x",
        tags=["python", "django"],
    )
    assert job_matches_keywords(job, ["python"]) is True  # matches a tag
    assert job_matches_keywords(job, ["backend"]) is True  # matches the title
    assert job_matches_keywords(job, ["rust", "golang"]) is False
    assert job_matches_keywords(job, ["PYTHON".lower()]) is True
