"""Evidence-only explanations for the defensive email risk engine."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExplanationResult(BaseModel):
    """Human-readable explanation generated from recorded analysis evidence."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    reasons: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


_DOMAIN_EVIDENCE = {
    "has_ip_address": "The URL uses an IP address instead of a conventional domain name.",
    "has_at_symbol": "The URL contains an @ symbol, which can obscure the true destination.",
    "suspicious_shortening_pattern": "The URL uses a known shortening pattern that hides its destination.",
    "insecure_transport": "The URL uses HTTP instead of HTTPS.",
    "long_url": "The URL is unusually long.",
    "many_subdomains": "The URL contains several subdomain levels.",
}


def generate_explanation(risk_result: Mapping[str, Any]) -> ExplanationResult:
    """Generate text only for evidence present in ``risk_result``.

    Unknown indicator codes are intentionally ignored. This prevents the
    explanation layer from making claims that are not backed by a known
    analyzer finding.
    """
    indicators = risk_result.get("detected_indicators", [])
    if not isinstance(indicators, Sequence) or isinstance(indicators, (str, bytes)):
        indicators = []

    reasons: list[str] = []
    action_keys: set[str] = set()
    url_predictions = _url_predictions(risk_result)

    for indicator in indicators:
        if not isinstance(indicator, Mapping):
            continue
        code = str(indicator.get("code", "")).casefold()
        details = indicator.get("details")
        details = details if isinstance(details, Mapping) else {}
        reason, actions = _reason_for_indicator(code, details, url_predictions)
        if reason and reason not in reasons:
            reasons.append(reason)
        action_keys.update(actions)

    classification = str(risk_result.get("classification", "")).upper()
    score = _score_text(risk_result.get("score"))
    if reasons and classification in {"SUSPICIOUS", "PHISHING"}:
        action_keys.add("report")
    if reasons:
        score_text = f" with a risk score of {score:.2f}" if score is not None else ""
        summary = (
            f"The {classification or 'available'} classification is supported by "
            f"{len(reasons)} observed security indicator(s){score_text}."
        )
    else:
        summary = "No specific suspicious evidence was produced by the available analyzers."

    return ExplanationResult(
        summary=summary,
        reasons=reasons,
        recommended_actions=_actions_in_order(action_keys),
    )


def explain_risk(risk_result: Mapping[str, Any]) -> ExplanationResult:
    """Descriptive alias for callers passing a risk-engine result."""
    return generate_explanation(risk_result)


def _reason_for_indicator(
    code: str,
    details: Mapping[str, Any],
    url_predictions: Mapping[str, Mapping[str, Any]],
) -> tuple[str | None, set[str]]:
    if code in {"spf_fail", "dkim_fail", "dmarc_fail"}:
        method = code.split("_", 1)[0].upper()
        return f"{method} authentication failed according to the Authentication-Results header.", {"verify_sender"}

    if code == "reply_to_mismatch":
        return "The From and Reply-To addresses do not match.", {"verify_sender"}

    if code == "authentication_identity_mismatch":
        return "An authentication identity does not match the From domain.", {"verify_sender"}

    if code == "return_path_mismatch":
        return "The Return-Path domain does not match the From domain.", {"verify_sender"}

    if code in {"spf_result_conflict", "dkim_result_conflict", "dmarc_result_conflict"}:
        method = code.split("_", 1)[0].upper()
        return f"The Authentication-Results header contains conflicting {method} outcomes.", {"verify_sender"}

    if code == "url_model_risk":
        url = str(details.get("url", "")).strip()
        prediction = url_predictions.get(url)
        if prediction:
            probability = _score_text(prediction.get("probability"))
            classification = str(prediction.get("classification", "suspicious")).casefold()
            if probability is not None:
                return (
                    f"The URL {url or 'provided'} was classified as {classification} "
                    f"with probability {probability:.0f}%.",
                    {"avoid_links"},
                )
        return f"A suspicious URL finding was produced{f' for {url}' if url else ''}.", {"avoid_links"}

    if code in _DOMAIN_EVIDENCE:
        url = str(details.get("url", "")).strip()
        reason = _DOMAIN_EVIDENCE[code]
        return (f"{reason}{f' URL: {url}.' if url else ''}", {"avoid_links"})

    if code == "urgency":
        return "Urgency language was detected in the message.", {"verify_sender"}

    if code == "credential_request":
        return "The message requests or references account credentials.", {"avoid_credentials"}

    if code in {"threat_or_consequence", "authority_or_secrecy"}:
        return "The message uses social-engineering pressure or authority cues.", {"verify_sender"}

    if code == "action_link_request":
        return "The message asks the recipient to follow an action link or button.", {"avoid_links"}

    return None, set()


def _url_predictions(risk_result: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    components = risk_result.get("components", {})
    if not isinstance(components, Mapping):
        return {}
    url_component = components.get("url", {})
    if not isinstance(url_component, Mapping):
        return {}
    details = url_component.get("details", {})
    if not isinstance(details, Mapping):
        return {}
    predictions = details.get("predictions", [])
    if not isinstance(predictions, Sequence) or isinstance(predictions, (str, bytes)):
        return {}
    return {
        str(prediction.get("url")): prediction
        for prediction in predictions
        if isinstance(prediction, Mapping) and prediction.get("url")
    }


def _score_text(value: Any) -> float | None:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score != score or score < 0:
        return None
    if score <= 1:
        return score * 100
    return min(score, 100)


def _actions_in_order(action_keys: set[str]) -> list[str]:
    actions = {
        "avoid_links": "Do not click suspicious links.",
        "avoid_credentials": "Do not submit credentials.",
        "verify_sender": "Verify the sender through an independent official channel.",
        "report": "Report or quarantine the email.",
    }
    ordered_keys = ("avoid_links", "avoid_credentials", "verify_sender", "report")
    return [actions[key] for key in ordered_keys if key in action_keys]
