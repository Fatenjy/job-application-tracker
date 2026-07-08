# Job Application Tracker

[![CI](https://github.com/Fatenjy/job-application-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/Fatenjy/job-application-tracker/actions/workflows/ci.yml)

**Live demo:** [job-application-tracker-ws8w.onrender.com](https://job-application-tracker-ws8w.onrender.com) — Kanban dashboard + [API docs](https://job-application-tracker-ws8w.onrender.com/docs) *(free tier — first request may take ~1 min to wake the service)*

A job-hunting assistant that **scrapes job listings from public APIs, stores them in PostgreSQL, filters them against your keywords, and emails you the new matches** — with a REST API to browse offers and track your applications from `saved` to `offer`.

Built as a first portfolio project with a deliberately production-grade stack: FastAPI, SQLAlchemy 2.0, Alembic migrations, Docker, APScheduler, pytest, and GitHub Actions CI.

## How it works

```
   every 6 hours                         your keywords
        |                              (python, junior, ...)
        v                                      |
  [3 scrapers] ---> [PostgreSQL] ---> [keyword filter] ---> email digest
   RemoteOK          dedup by                 |
   Arbeitnow         (source,          [FastAPI REST API]
   Remotive          external_id)      /jobs /applications /docs
```

- **Scrapers** pull from legal public APIs (no LinkedIn/Indeed scraping) and normalize each source's format into one schema.
- **Ingestion is idempotent**: a unique `(source, external_id)` constraint plus `ON CONFLICT DO NOTHING ... RETURNING` means re-scraping never duplicates and new jobs are detected exactly.
- **Notifications**: new jobs matching `MATCH_KEYWORDS` are emailed (SMTP) and/or sent via Telegram — whichever is configured.
- **Application tracking**: one application per job, status workflow `saved → applied → interview → offer/rejected`.
- **Dashboard**: a dependency-free HTML/CSS/JS Kanban board served by the same FastAPI app — drag cards between status columns, search listings, keep notes per application.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| API | FastAPI + Uvicorn | Modern async framework, automatic OpenAPI docs |
| Database | PostgreSQL 16 (Docker) | The industry-default relational database; JSONB for tags |
| ORM / migrations | SQLAlchemy 2.0 + Alembic | Typed `Mapped[]` models, versioned reversible migrations |
| Scheduling | APScheduler | In-process interval jobs tied to the FastAPI lifespan |
| HTTP client | httpx | Modern client used by the scrapers |
| Quality | pytest, ruff, GitHub Actions | 11 tests against a real PostgreSQL service container |

## Quickstart

Requires Python 3.12+, Docker Desktop, and Git.

```bash
git clone https://github.com/<you>/job-application-tracker.git
cd job-application-tracker

# 1. Configuration
cp .env.example .env        # then edit values (DB password, keywords, SMTP)

# 2. Database
docker compose up -d db

# 3. Python environment
python -m venv .venv
.venv/Scripts/activate      # Windows — on Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"

# 4. Create the schema
alembic upgrade head

# 5. Run
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API documentation.

Trigger a scrape manually (also runs automatically every `SCRAPE_INTERVAL_HOURS`):

```bash
python -m app.services.ingest
```

## Configuration

All configuration lives in `.env` (never committed — see `.env.example`):

| Variable | Purpose |
|---|---|
| `POSTGRES_*` | Database credentials and host |
| `MATCH_KEYWORDS` | Comma-separated keywords that trigger notifications |
| `SCRAPE_INTERVAL_HOURS` | How often the scheduler scrapes (default 6) |
| `SMTP_*`, `NOTIFY_EMAIL_TO` | Email notifications (e.g. Gmail + app password) |
| `TELEGRAM_*` | Optional Telegram notifications |

## API overview

| Endpoint | Description |
|---|---|
| `GET /health` | Liveness check (verifies DB connectivity) |
| `GET /jobs?q=python&tag=data&remote=true&source=remotive` | Search and filter listings |
| `GET /jobs/{id}` | One listing |
| `POST /applications` | Start tracking an application (409 on duplicates) |
| `GET /applications` | Your applications with the listing embedded |
| `PATCH /applications/{id}` | Update status/notes (partial update) |
| `DELETE /applications/{id}` | Stop tracking |

## Tests

```bash
pytest
```

Tests run against a dedicated `jobtracker_test` database created on the fly — real data is never touched. Scraper tests replay recorded API payloads, so no network is needed. The same suite runs in CI on every push, against a real PostgreSQL service container.

## Adding a job source

The architecture makes new sources cheap (see `app/scrapers/`): implement the
`JobSource` protocol — a `name` and a `fetch() -> list[JobCreate]` that
translates the source's JSON into the normalized schema — then register the
scraper in `SCRAPERS` (`app/services/ingest.py`). Dedup, storage, API, and
notifications need no changes.

## Roadmap

- [x] Public deployment with a live demo (Render + Neon PostgreSQL)
- [x] Kanban dashboard on top of the API (vanilla JS, drag & drop)
- [ ] More sources (The Muse, Jobicy, WeWorkRemotely)
- [ ] Celery + Redis for distributed scraping (v2)
