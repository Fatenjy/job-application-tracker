"""Auth tests: registration, login, and token validation."""


def test_register_returns_token(client):
    res = client.post("/auth/register", json={"email": "a@b.com", "password": "password123"})
    assert res.status_code == 201
    assert res.json()["token_type"] == "bearer"
    assert res.json()["access_token"]


def test_register_duplicate_email(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "password123"})
    dup = client.post("/auth/register", json={"email": "a@b.com", "password": "password123"})
    assert dup.status_code == 409


def test_register_rejects_short_password(client):
    res = client.post("/auth/register", json={"email": "a@b.com", "password": "short"})
    assert res.status_code == 422  # schema enforces min length


def test_register_rejects_invalid_email(client):
    res = client.post("/auth/register", json={"email": "not-an-email", "password": "password123"})
    assert res.status_code == 422


def test_login_and_me(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "password123"})

    # OAuth2 password flow uses form fields; username = email
    login = client.post("/auth/token", data={"username": "a@b.com", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "a@b.com"


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "password123"})
    bad = client.post("/auth/token", data={"username": "a@b.com", "password": "wrongpass"})
    assert bad.status_code == 401


def test_me_rejects_bad_token(client):
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
