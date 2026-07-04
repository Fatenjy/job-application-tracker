"""Scraper tests: no network involved — we feed each scraper a fake HTTP
response copied from the real API format, and check the translation to our
normalized JobCreate. Fast, deterministic, and they still catch any format
regression in OUR parsing code."""

from app.scrapers.arbeitnow import ArbeitnowScraper
from app.scrapers.remoteok import RemoteOKScraper
from app.scrapers.remotive import RemotiveScraper


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_remoteok_skips_legal_notice_and_normalizes(monkeypatch):
    payload = [
        {"legal": "API Terms of Service..."},
        {
            "id": "1134410",
            "position": "Product Manager",
            "company": "TMEIC",
            "location": "",
            "url": "https://remoteok.com/l/1134410",
            "epoch": 1783036804,
            "tags": ["product", "exec"],
        },
    ]
    monkeypatch.setattr(
        "app.scrapers.remoteok.httpx.get", lambda *a, **k: FakeResponse(payload)
    )
    jobs = RemoteOKScraper().fetch()

    assert len(jobs) == 1  # the legal notice was skipped
    job = jobs[0]
    assert job.source == "remoteok"
    assert job.external_id == "1134410"
    assert job.title == "Product Manager"
    assert job.remote is True
    assert job.location is None  # empty string becomes None
    assert job.posted_at is not None


def test_arbeitnow_normalizes_fields(monkeypatch):
    payload = {
        "data": [
            {
                "slug": "dev-berlin-123",
                "company_name": "ACME GmbH",
                "title": "Junior Developer",
                "remote": False,
                "url": "https://arbeitnow.com/jobs/dev-berlin-123",
                "tags": ["python"],
                "location": "Berlin",
                "created_at": 1783113612,
            }
        ]
    }
    monkeypatch.setattr(
        "app.scrapers.arbeitnow.httpx.get", lambda *a, **k: FakeResponse(payload)
    )
    jobs = ArbeitnowScraper().fetch()

    assert len(jobs) == 1
    job = jobs[0]
    assert job.source == "arbeitnow"
    assert job.external_id == "dev-berlin-123"
    assert job.company == "ACME GmbH"
    assert job.remote is False
    assert job.location == "Berlin"


def test_remotive_parses_iso_date(monkeypatch):
    payload = {
        "jobs": [
            {
                "id": 2090942,
                "title": "Data Analyst",
                "company_name": "Clerky",
                "candidate_required_location": "Worldwide",
                "url": "https://remotive.com/j/2090942",
                "publication_date": "2026-07-02T07:39:11",
                "tags": ["data"],
            }
        ]
    }
    monkeypatch.setattr(
        "app.scrapers.remotive.httpx.get", lambda *a, **k: FakeResponse(payload)
    )
    jobs = RemotiveScraper().fetch()

    assert len(jobs) == 1
    job = jobs[0]
    assert job.external_id == "2090942"
    assert job.posted_at is not None
    assert job.posted_at.tzinfo is not None  # timezone was attached
