from tests.conftest import PASSWORD, create_user, login
from app.models import UserRole


def test_register_creates_employee(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "email": "new@example.com", "password": PASSWORD},
    )
    assert response.status_code == 201
    assert response.json()["role"] == "employee"
    assert "hashed_password" not in response.json()


def test_register_rejects_weak_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "email": "new@example.com", "password": "abcdefgh"},
    )
    assert response.status_code == 422


def test_login_wrong_password(client, db):
    create_user(db, UserRole.admin)
    response = client.post("/api/v1/auth/login", data={"username": "admin", "password": "wrong"})
    assert response.status_code == 401


def test_refresh_rotates_and_detects_reuse(client, db):
    create_user(db, UserRole.admin)
    tokens = login(client, "admin")
    first = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert first.status_code == 200
    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reuse.status_code == 401
    after_reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": first.json()["refresh_token"]})
    assert after_reuse.status_code == 401


def test_logout_revokes_refresh_token(client, db):
    create_user(db, UserRole.admin)
    tokens = login(client, "admin")
    assert client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 204
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_refresh_token_cannot_access_api(client, db):
    create_user(db, UserRole.admin)
    tokens = login(client, "admin")
    response = client.get("/api/v1/products", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert response.status_code == 401
