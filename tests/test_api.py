"""API tests: real HTTP requests through FastAPI's TestClient, hitting the
test database. This is the closest thing to a user actually using the API."""

from app.models import Job


def make_job(db, **overrides) -> Job:
    defaults = {
        "source": "test",
        "external_id": "job-1",
        "title": "Junior Python Developer",
        "company": "ACME",
        "url": "https://example.com/job-1",
        "remote": True,
        "tags": ["python", "junior"],
    }
    job = Job(**{**defaults, **overrides})
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_list_jobs_empty(client):
    assert client.get("/jobs").json() == []


def test_list_jobs_filters(client, db):
    make_job(db, external_id="a", title="Junior Python Developer", remote=True)
    make_job(db, external_id="b", title="Senior Java Engineer", remote=False, tags=["java"])

    assert len(client.get("/jobs").json()) == 2
    # text search on title
    assert len(client.get("/jobs", params={"q": "python"}).json()) == 1
    # remote filter
    assert len(client.get("/jobs", params={"remote": False}).json()) == 1
    # JSONB tag containment
    assert len(client.get("/jobs", params={"tag": "python"}).json()) == 1
    # combination with no possible match
    assert client.get("/jobs", params={"q": "python", "remote": False}).json() == []


def test_get_job_404(client):
    assert client.get("/jobs/9999").status_code == 404


def test_application_lifecycle(client, db):
    job = make_job(db)

    # create
    created = client.post("/applications", json={"job_id": job.id, "notes": "fit!"})
    assert created.status_code == 201
    app_id = created.json()["id"]
    assert created.json()["status"] == "saved"
    assert created.json()["job"]["title"] == job.title  # job comes embedded

    # duplicate is refused with 409 Conflict
    assert client.post("/applications", json={"job_id": job.id}).status_code == 409

    # unknown job is refused with 404
    assert client.post("/applications", json={"job_id": 9999}).status_code == 404

    # partial update
    patched = client.patch(f"/applications/{app_id}", json={"status": "applied"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "applied"
    assert patched.json()["notes"] == "fit!"  # untouched by the PATCH

    # invalid status is rejected by schema validation
    assert (
        client.patch(f"/applications/{app_id}", json={"status": "hired!!"}).status_code
        == 422
    )

    # delete, then it is really gone
    assert client.delete(f"/applications/{app_id}").status_code == 204
    assert client.delete(f"/applications/{app_id}").status_code == 404
    assert client.get("/applications").json() == []
