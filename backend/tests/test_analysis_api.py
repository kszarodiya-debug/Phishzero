import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api import analysis as analysis_api
from app.db.database import Base, get_db
from app.main import app


TEST_SECRET = "test-only-analysis-secret-key-that-is-at-least-32-characters"


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
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


def _register_and_login(client: TestClient, email: str) -> dict[str, str]:
    registration = client.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass123!"},
    )
    assert registration.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _risk_result() -> dict[str, object]:
    return {
        "score": 82.5,
        "classification": "PHISHING",
        "confidence": 0.91,
        "component_scores": {
            "text": 88.0,
            "url": 90.0,
            "headers": 75.0,
            "domain_security": 90.0,
            "social_engineering": 80.0,
        },
        "components": {
            "text": {"details": {"model_version": "test-text-v1"}},
            "url": {
                "details": {
                    "predictions": [
                        {
                            "url": "https://example.com/verify",
                            "classification": "phishing",
                            "probability": 0.9,
                            "score": 90.0,
                        }
                    ]
                }
            },
        },
        "detected_indicators": [
            {
                "code": "reply_to_mismatch",
                "category": "headers",
                "severity": "medium",
                "message": "Reply-To does not match the From mailbox.",
                "details": {},
            },
            {
                "code": "url_model_risk",
                "category": "url",
                "severity": "high",
                "message": "The URL model identified a phishing URL.",
                "details": {"url": "https://example.com/verify"},
            },
        ],
        "calculation": {"formula": "test calculation"},
        "explanation": "Test risk explanation.",
        "errors": [],
    }


def _analysis_payload() -> dict[str, object]:
    return {
        "sender": "sender@example.com",
        "recipients": ["analyst@example.com"],
        "subject": "Urgent account verification",
        "body_text": "Verify your account at https://example.com/verify.",
        "raw_headers": [
            {"name": "From", "value": "sender@example.com"},
            {"name": "Reply-To", "value": "different@example.net"},
        ],
    }


def test_successful_analysis_persists_and_returns_results(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(analysis_api, "assess_risk", lambda **kwargs: _risk_result())
    headers = _register_and_login(client, "owner@example.com")

    response = client.post("/api/analysis", headers=headers, json=_analysis_payload())

    assert response.status_code == 201
    result = response.json()
    assert result["analysis_id"] > 0
    assert result["classification"] == "PHISHING"
    assert result["security_type"] == "UNSAFE"
    assert result["risk_score"] == 82.5
    assert result["confidence"] == 0.91
    assert result["text_score"] == 88
    assert result["url_score"] == 90
    assert result["header_score"] == 75
    assert result["analyzed_urls"] == ["https://example.com/verify"]
    assert result["model_version"] == "test-text-v1"
    assert len(result["threats"]) == 2
    assert "From and Reply-To" in " ".join(result["reasons"])
    assert any("classified as phishing" in reason for reason in result["reasons"])
    assert "Do not click suspicious links." in result["recommended_actions"]
    assert "Report or quarantine the email." in result["recommended_actions"]


def test_unauthorized_analysis_request(client: TestClient) -> None:
    response = client.post("/api/analysis", json=_analysis_payload())

    assert response.status_code == 401


def test_invalid_analysis_input(client: TestClient) -> None:
    headers = _register_and_login(client, "invalid-input@example.com")
    payload = _analysis_payload()
    payload["sender"] = "not-an-email"
    payload["recipients"] = []

    response = client.post("/api/analysis", headers=headers, json=payload)

    assert response.status_code == 422


def test_retrieving_own_analysis(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(analysis_api, "assess_risk", lambda **kwargs: _risk_result())
    headers = _register_and_login(client, "retriever@example.com")
    created = client.post("/api/analysis", headers=headers, json=_analysis_payload()).json()

    response = client.get(f"/api/analysis/{created['analysis_id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["analysis_id"] == created["analysis_id"]
    assert "body_text" not in response.json()


def test_user_cannot_retrieve_another_users_analysis(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(analysis_api, "assess_risk", lambda **kwargs: _risk_result())
    owner_headers = _register_and_login(client, "first-owner@example.com")
    created = client.post(
        "/api/analysis",
        headers=owner_headers,
        json=_analysis_payload(),
    ).json()
    other_headers = _register_and_login(client, "second-owner@example.com")

    response = client.get(
        f"/api/analysis/{created['analysis_id']}",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_history_returns_only_current_users_records(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(analysis_api, "assess_risk", lambda **kwargs: _risk_result())
    owner_headers = _register_and_login(client, "history-owner@example.com")
    other_headers = _register_and_login(client, "history-other@example.com")
    first = client.post("/api/analysis", headers=owner_headers, json=_analysis_payload())
    second = client.post("/api/analysis", headers=owner_headers, json=_analysis_payload())
    assert first.status_code == 201
    assert second.status_code == 201

    owner_history = client.get("/api/analysis/history", headers=owner_headers)
    other_history = client.get("/api/analysis/history", headers=other_headers)

    assert owner_history.status_code == 200
    assert len(owner_history.json()) == 2
    assert other_history.status_code == 200
    assert other_history.json() == []

