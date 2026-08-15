import pytest
from fastapi.testclient import TestClient

from app.api import public_analysis as public_analysis_api
from app.main import app


TEST_SECRET = "test-only-public-analysis-secret-key-at-least-32-characters"


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
    monkeypatch.setenv("FRONTEND_ORIGINS", "http://localhost:5173")
    with TestClient(app) as test_client:
        yield test_client


def _payload() -> dict[str, object]:
    return {
        "sender": "sender@example.com",
        "recipients": ["recipient@example.com"],
        "subject": "Urgent account verification",
        "body_text": "Verify your account immediately at https://example.com/verify.",
        "raw_headers": [],
    }


def test_public_analysis_returns_feedback_without_authentication(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        public_analysis_api,
        "assess_risk",
        lambda **_kwargs: {
            "score": 82.5,
            "classification": "PHISHING",
            "confidence": 0.91,
            "component_scores": {"text": 88, "url": 90, "headers": 75},
            "components": {
                "text": {"details": {"model_version": "test-text-v1"}},
            },
            "detected_indicators": [
                {
                    "code": "urgency",
                    "category": "social_engineering",
                    "severity": "medium",
                    "message": "Urgency language was detected.",
                    "details": {},
                }
            ],
        },
    )

    response = client.post("/api/public/analysis", json=_payload())

    assert response.status_code == 200
    result = response.json()
    assert result["classification"] == "PHISHING"
    assert result["risk_score"] == 82.5
    assert result["text_score"] == 88
    assert result["analyzed_urls"] == ["https://example.com/verify"]
    assert result["model_version"] == "test-text-v1"
    assert "Urgency language" in " ".join(result["reasons"])
    assert "analysis_id" not in result


def test_public_analysis_validates_input_without_authentication(client: TestClient) -> None:
    payload = _payload()
    payload["sender"] = "not-an-email"

    response = client.post("/api/public/analysis", json=payload)

    assert response.status_code == 422
