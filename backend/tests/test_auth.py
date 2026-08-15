import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app


TEST_SECRET = "test-only-secret-key-that-is-at-least-32-characters"


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def registration_payload(email: str = "analyst@example.com") -> dict[str, str]:
    return {
        "email": email,
        "password": "SecurePass123!",
        "display_name": "Security Analyst",
    }


def register_user(client: TestClient, email: str = "analyst@example.com") -> dict:
    response = client.post("/api/auth/register", json=registration_payload(email))
    assert response.status_code == 201
    return response.json()


def login_user(client: TestClient, email: str = "analyst@example.com") -> dict:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    assert response.status_code == 200
    return response.json()


def test_successful_registration(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json=registration_payload(),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "analyst@example.com"
    assert body["display_name"] == "Security Analyst"
    assert "password_hash" not in body
    assert "password" not in body


def test_duplicate_email(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/auth/register",
        json=registration_payload("ANALYST@example.com"),
    )

    assert response.status_code == 409


def test_successful_login(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/auth/login",
        json={"email": "analyst@example.com", "password": "SecurePass123!"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_wrong_password(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/auth/login",
        json={"email": "analyst@example.com", "password": "WrongPass123!"},
    )

    assert response.status_code == 401


def test_missing_token(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_invalid_token(client: TestClient) -> None:
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401


def test_valid_token(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200


def test_current_user_retrieval(client: TestClient) -> None:
    registered_user = register_user(client)
    token = login_user(client)["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == registered_user["id"]
    assert response.json()["email"] == "analyst@example.com"
    assert "password_hash" not in response.json()

