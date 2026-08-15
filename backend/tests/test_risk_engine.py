from pathlib import Path

from app.services import risk_engine


def _headers(*states: str) -> dict[str, object]:
    methods = ("SPF", "DKIM", "DMARC")
    return {
        "authentication": {
            method: {"state": state, "evidence": []}
            for method, state in zip(methods, states or ("PASS", "PASS", "PASS"))
        },
        "findings": [],
    }


def _stub_models(monkeypatch, *, text: dict[str, object], url: dict[str, object] | None = None) -> None:
    monkeypatch.setattr(
        risk_engine,
        "predict_email_text",
        lambda subject, body, model_path: text,
    )
    if url is not None:
        monkeypatch.setattr(
            risk_engine,
            "analyze_url",
            lambda value, model_path: url,
        )


def test_safe_email(monkeypatch) -> None:
    _stub_models(
        monkeypatch,
        text={"class": "ham", "probability": 0.95, "model_version": "test"},
        url={"classification": "benign", "probability": 0.95},
    )
    monkeypatch.setattr(risk_engine, "analyze_headers", lambda headers: _headers())

    result = risk_engine.assess_risk(
        "Team meeting agenda",
        "The meeting starts at ten.",
        ["https://www.example.com/agenda"],
        {"From": "colleague@example.com"},
    )

    assert result["classification"] == "SAFE"
    assert result["score"] <= 25
    assert result["confidence"] > 0
    assert result["errors"] == []


def test_spam_like_email_is_low_risk(monkeypatch) -> None:
    _stub_models(
        monkeypatch,
        text={"class": "spam", "probability": 0.70, "model_version": "test"},
    )
    monkeypatch.setattr(risk_engine, "analyze_headers", lambda headers: _headers())

    result = risk_engine.assess_risk(
        "Free gift card waiting",
        "Claim your reward today.",
        [],
        {"From": "offers@example.com"},
    )

    assert result["classification"] == "LOW_RISK"
    assert any(indicator["code"] == "financial_or_prize_lure" for indicator in result["detected_indicators"])


def test_suspicious_email_combines_social_and_header_signals(monkeypatch) -> None:
    _stub_models(
        monkeypatch,
        text={"class": "spam", "probability": 0.80, "model_version": "test"},
        url={"classification": "suspicious", "probability": 0.65},
    )
    monkeypatch.setattr(
        risk_engine,
        "analyze_headers",
        lambda headers: _headers("UNKNOWN", "PASS", "PASS"),
    )

    result = risk_engine.assess_risk(
        "Urgent account verification",
        "Verify your account immediately by clicking the link.",
        ["http://secure.example.com/update"],
        {"From": "sender@example.com"},
    )

    assert result["classification"] == "SUSPICIOUS"
    assert 50 < result["score"] <= 75
    assert result["component_scores"]["headers"] == 30


def test_phishing_email_reaches_phishing_classification(monkeypatch) -> None:
    _stub_models(
        monkeypatch,
        text={"class": "spam", "probability": 0.98, "model_version": "test"},
        url={"classification": "phishing", "probability": 0.95},
    )
    monkeypatch.setattr(
        risk_engine,
        "analyze_headers",
        lambda headers: _headers("FAIL", "FAIL", "FAIL"),
    )

    result = risk_engine.assess_risk(
        "Urgent account warning",
        "Your account will be closed unless you verify your password immediately.",
        ["http://secure-login.example.com@198.51.100.7/verify"],
        {"From": "sender@example.com"},
    )

    assert result["classification"] == "PHISHING"
    assert result["score"] >= 76
    assert {"text", "url", "headers", "domain_security", "social_engineering"}.issubset(
        result["calculation"]["available_components"]
    )


def test_missing_text_model_does_not_crash(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(risk_engine, "analyze_headers", lambda headers: _headers())

    result = risk_engine.assess_risk(
        "Routine notice",
        "This is a routine notice.",
        [],
        {"From": "sender@example.com"},
        text_model_path=tmp_path / "missing-text-model.joblib",
    )

    assert result["component_scores"]["text"] is None
    assert any(error["component"] == "text" for error in result["errors"])
    assert result["classification"] in {"SAFE", "LOW_RISK", "SUSPICIOUS", "PHISHING"}


def test_missing_url_is_reported_without_crashing(monkeypatch) -> None:
    _stub_models(
        monkeypatch,
        text={"class": "ham", "probability": 0.95, "model_version": "test"},
    )
    monkeypatch.setattr(risk_engine, "analyze_headers", lambda headers: _headers())

    result = risk_engine.assess_risk(
        "Routine notice",
        "This is a routine notice.",
        None,
        {"From": "sender@example.com"},
    )

    assert result["component_scores"]["url"] is None
    assert result["component_scores"]["domain_security"] is None
    assert result["calculation"]["available_weight"] == 0.6


def test_missing_headers_is_reported_without_crashing(monkeypatch) -> None:
    _stub_models(
        monkeypatch,
        text={"class": "ham", "probability": 0.95, "model_version": "test"},
    )

    result = risk_engine.assess_risk("Routine notice", "This is routine.", [], None)

    assert result["component_scores"]["headers"] is None
    assert any(
        error["component"] == "headers" and error["code"] == "missing_input"
        for error in result["errors"]
    )


def test_conflicting_text_and_url_signals_are_explained(monkeypatch) -> None:
    _stub_models(
        monkeypatch,
        text={"class": "ham", "probability": 0.95, "model_version": "test"},
        url={"classification": "phishing", "probability": 0.95},
    )
    monkeypatch.setattr(risk_engine, "analyze_headers", lambda headers: _headers())

    result = risk_engine.assess_risk(
        "Project update",
        "The project update is attached.",
        ["https://198.51.100.7/login"],
        {"From": "sender@example.com"},
    )

    assert result["component_scores"]["text"] == 5
    assert result["component_scores"]["url"] == 95
    assert result["classification"] == "LOW_RISK"
    assert 26 < result["score"] <= 50
    assert "normalized weighted average" in result["explanation"]
    assert result["calculation"]["formula"].startswith("sum(component_score")
