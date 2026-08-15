from app.services.explanation_engine import generate_explanation


def _indicator(code: str, *, url: str | None = None) -> dict[str, object]:
    return {
        "code": code,
        "category": "test",
        "severity": "high",
        "message": "test evidence",
        "details": {"url": url} if url else {},
    }


def test_explanation_reasons_match_actual_evidence() -> None:
    result = generate_explanation(
        {
            "classification": "PHISHING",
            "score": 88,
            "detected_indicators": [
                _indicator("spf_fail"),
                _indicator("dkim_fail"),
                _indicator("dmarc_fail"),
                _indicator("reply_to_mismatch"),
                _indicator("urgency"),
                _indicator("credential_request"),
                _indicator("has_ip_address", url="http://198.51.100.7/login"),
                _indicator("suspicious_shortening_pattern", url="https://bit.ly/verify"),
                _indicator("url_model_risk", url="https://bit.ly/verify"),
            ],
            "components": {
                "url": {
                    "details": {
                        "predictions": [
                            {
                                "url": "https://bit.ly/verify",
                                "classification": "phishing",
                                "probability": 0.93,
                            }
                        ]
                    }
                }
            },
        }
    )

    assert "SPF authentication failed" in " ".join(result.reasons)
    assert "DKIM authentication failed" in " ".join(result.reasons)
    assert "DMARC authentication failed" in " ".join(result.reasons)
    assert any("From and Reply-To" in reason for reason in result.reasons)
    assert any("Urgency language" in reason for reason in result.reasons)
    assert any("credentials" in reason for reason in result.reasons)
    assert any("IP address" in reason for reason in result.reasons)
    assert any("shortening pattern" in reason for reason in result.reasons)
    assert any("93%" in reason for reason in result.reasons)
    assert "Do not click suspicious links." in result.recommended_actions
    assert "Do not submit credentials." in result.recommended_actions
    assert "Verify the sender through an independent official channel." in result.recommended_actions
    assert "Report or quarantine the email." in result.recommended_actions


def test_explanation_does_not_invent_evidence() -> None:
    result = generate_explanation(
        {
            "classification": "PHISHING",
            "score": 99,
            "detected_indicators": [],
            "components": {
                "url": {
                    "details": {
                        "predictions": [
                            {
                                "url": "https://example.com",
                                "classification": "phishing",
                                "probability": 0.99,
                            }
                        ]
                    }
                }
            },
        }
    )

    assert result.reasons == []
    assert result.recommended_actions == []
    assert "No specific suspicious evidence" in result.summary


def test_unknown_indicators_are_not_presented_as_facts() -> None:
    result = generate_explanation(
        {
            "classification": "SUSPICIOUS",
            "detected_indicators": [_indicator("future_unverified_indicator")],
        }
    )

    assert result.reasons == []
    assert result.recommended_actions == []
