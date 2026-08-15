"""Centralized, offline risk scoring for analyzed email content.

This module combines the existing local text and URL models with the existing
header analyzer and deterministic social-engineering indicators. It never
visits URLs, performs DNS lookups, sends email, or executes email content.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import math
import re
from typing import Any

from app.ml.predict import MODEL_PATH as TEXT_MODEL_PATH
from app.ml.predict import predict_email_text
from app.services.header_analyzer import HeaderAnalysisResult, analyze_headers
from app.services.url_analyzer import URL_MODEL_PATH, analyze_url, extract_url_features


COMPONENT_NAMES = ("text", "url", "headers", "domain_security", "social_engineering")


@dataclass(frozen=True)
class ClassificationThreshold:
    """Inclusive upper bound for one risk classification."""

    label: str
    maximum_score: float


@dataclass(frozen=True)
class SocialEngineeringRule:
    """Configured deterministic indicator used by the social-engineering scorer."""

    code: str
    pattern: str
    score: float
    severity: str
    message: str


@dataclass(frozen=True)
class RiskConfig:
    """All risk weights, thresholds, and signal scores in one location."""

    component_weights: Mapping[str, float]
    classification_thresholds: tuple[ClassificationThreshold, ...]
    text_risk_labels: frozenset[str]
    text_safe_labels: frozenset[str]
    url_risk_labels: frozenset[str]
    url_safe_labels: frozenset[str]
    header_state_scores: Mapping[str, float]
    header_finding_scores: Mapping[str, float]
    domain_feature_scores: Mapping[str, float]
    domain_insecure_transport_score: float
    domain_long_url_length: int
    domain_long_url_score: float
    domain_subdomain_threshold: int
    domain_subdomain_score: float
    social_rules: tuple[SocialEngineeringRule, ...]

    def __post_init__(self) -> None:
        if set(self.component_weights) != set(COMPONENT_NAMES):
            raise ValueError("Risk configuration must define every risk component weight")
        if any(weight < 0 for weight in self.component_weights.values()):
            raise ValueError("Risk component weights cannot be negative")
        if sum(self.component_weights.values()) <= 0:
            raise ValueError("Risk component weights must have a positive total")
        if not self.classification_thresholds:
            raise ValueError("At least one classification threshold is required")
        maximums = [threshold.maximum_score for threshold in self.classification_thresholds]
        if maximums != sorted(maximums) or maximums[-1] < 100:
            raise ValueError("Classification thresholds must be ordered through score 100")


# Change weights and thresholds here when calibrating the engine. Components
# are renormalized over available inputs so an absent model does not crash or
# silently contribute a false zero to the final score.
RISK_CONFIG = RiskConfig(
    component_weights={
        "text": 0.30,
        "url": 0.30,
        "headers": 0.20,
        "domain_security": 0.10,
        "social_engineering": 0.10,
    },
    classification_thresholds=(
        ClassificationThreshold("SAFE", 25),
        ClassificationThreshold("LOW_RISK", 50),
        ClassificationThreshold("SUSPICIOUS", 75),
        ClassificationThreshold("PHISHING", 100),
    ),
    text_risk_labels=frozenset({"spam", "phishing", "malicious", "suspicious"}),
    text_safe_labels=frozenset({"ham", "benign", "safe", "legitimate"}),
    url_risk_labels=frozenset({"phishing", "malicious", "suspicious"}),
    url_safe_labels=frozenset({"benign", "safe", "legitimate"}),
    header_state_scores={
        "PASS": 0,
        "FAIL": 80,
        "UNKNOWN": 30,
        "NOT_PRESENT": 0,
    },
    header_finding_scores={
        "reply_to_mismatch": 70,
        "authentication_identity_mismatch": 65,
        "spf_result_conflict": 75,
        "dkim_result_conflict": 75,
        "dmarc_result_conflict": 75,
        "return_path_mismatch": 45,
        "from_address_count": 45,
    },
    domain_feature_scores={
        "has_ip_address": 90,
        "has_at_symbol": 90,
        "suspicious_shortening_pattern": 70,
    },
    domain_insecure_transport_score=30,
    domain_long_url_length=120,
    domain_long_url_score=25,
    domain_subdomain_threshold=3,
    domain_subdomain_score=25,
    social_rules=(
        SocialEngineeringRule(
            code="urgency",
            pattern=r"\b(?:urgent|immediately|act now|as soon as possible|last chance|expires?)\b",
            score=35,
            severity="medium",
            message="The message uses urgency or a time limit to pressure action.",
        ),
        SocialEngineeringRule(
            code="credential_request",
            pattern=r"\b(?:verify|confirm|reset|password|credential|login|sign in|account)\b",
            score=40,
            severity="high",
            message="The message references account access or credential verification.",
        ),
        SocialEngineeringRule(
            code="threat_or_consequence",
            pattern=r"\b(?:suspend(?:ed)?|close(?:d)?|terminate|penalty|legal action|locked)\b",
            score=50,
            severity="high",
            message="The message threatens a negative consequence for not acting.",
        ),
        SocialEngineeringRule(
            code="financial_or_prize_lure",
            pattern=r"\b(?:prize|winner|reward|gift card|cash|investment|wire transfer|payment)\b",
            score=30,
            severity="medium",
            message="The message uses a financial or prize-related lure.",
        ),
        SocialEngineeringRule(
            code="authority_or_secrecy",
            pattern=r"\b(?:secret|confidential|ceo|director|executive)\b",
            score=45,
            severity="high",
            message="The message invokes authority or secrecy to influence the recipient.",
        ),
        SocialEngineeringRule(
            code="action_link_request",
            pattern=r"\b(?:click|open|follow)\b.{0,30}\b(?:link|url|button|here)\b",
            score=25,
            severity="medium",
            message="The message asks the recipient to follow an action link or button.",
        ),
    ),
)


HeaderInput = Mapping[str, str | Sequence[str]] | Iterable[Mapping[str, str] | Any]


def assess_risk(
    subject: str | None = None,
    body: str | None = None,
    urls: Sequence[str] | None = None,
    headers: HeaderInput | None = None,
    *,
    text_model_path: str | None = None,
    url_model_path: str | None = None,
    config: RiskConfig = RISK_CONFIG,
) -> dict[str, Any]:
    """Return a normalized risk score and an explanation of its components.

    Model and input failures are recorded in ``errors`` and make only the
    affected component unavailable. Available component weights are
    renormalized before calculating the final score.
    """
    normalized_subject = _coerce_text(subject)
    normalized_body = _coerce_text(body)
    errors: list[dict[str, str]] = []
    detected_indicators: list[dict[str, Any]] = []
    components = {
        name: {
            "score": None,
            "weight": float(config.component_weights[name]),
            "available": False,
            "contribution": 0.0,
            "details": {},
        }
        for name in COMPONENT_NAMES
    }

    if normalized_subject.strip() or normalized_body.strip():
        try:
            text_prediction = predict_email_text(
                normalized_subject,
                normalized_body,
                text_model_path or TEXT_MODEL_PATH,
            )
            text_score = _text_prediction_score(text_prediction, config)
            _set_component(
                components["text"],
                text_score,
                {
                    "class": str(text_prediction.get("class", "")),
                    "probability": _bounded_probability(text_prediction.get("probability", 0)),
                    "model_version": str(text_prediction.get("model_version", "")),
                },
            )
            if text_score >= 50:
                detected_indicators.append(
                    _indicator(
                        "text_model_risk",
                        "text",
                        "medium" if text_score < 75 else "high",
                        "The text model classified the message as spam-like or malicious.",
                        score=text_score,
                    )
                )
        except Exception as exc:  # component isolation is intentional
            _record_error(errors, "text", exc)
    else:
        _record_error(errors, "text", ValueError("No subject or body text was provided"), "missing_input")

    input_urls = _normalize_urls(urls, errors)
    valid_url_features: list[tuple[str, dict[str, int]]] = []
    url_scores: list[float] = []
    url_details: list[dict[str, Any]] = []
    for url in input_urls:
        try:
            features = extract_url_features(url)
            valid_url_features.append((url, features))
        except Exception as exc:  # malformed URLs must not stop other URLs
            _record_error(errors, "domain_security", exc, "invalid_url", url=url)
            continue

        try:
            url_prediction = analyze_url(url, url_model_path or URL_MODEL_PATH)
            score = _url_prediction_score(url_prediction, config)
            url_scores.append(score)
            url_details.append(
                {
                    "url": url,
                    "classification": str(url_prediction.get("classification", "")),
                    "probability": _bounded_probability(url_prediction.get("probability", 0)),
                    "score": round(score, 2),
                }
            )
            if score >= 50:
                detected_indicators.append(
                    _indicator(
                        "url_model_risk",
                        "url",
                        "medium" if score < 75 else "high",
                        "The URL model identified a suspicious or phishing URL.",
                        score=score,
                        url=url,
                    )
                )
        except Exception as exc:  # missing URL models are a supported state
            _record_error(errors, "url", exc, url=url)

    if url_scores:
        _set_component(
            components["url"],
            max(url_scores),
            {"url_count": len(url_scores), "predictions": url_details},
        )

    if valid_url_features:
        domain_scores = [
            _domain_feature_score(url, features, config, detected_indicators)
            for url, features in valid_url_features
        ]
        _set_component(
            components["domain_security"],
            max(domain_scores),
            {"url_count": len(valid_url_features)},
        )

    if headers is not None:
        try:
            header_result = analyze_headers(headers)
            header_score = _header_score(header_result, config, detected_indicators)
            _set_component(
                components["headers"],
                header_score,
                _header_details(header_result),
            )
        except Exception as exc:
            _record_error(errors, "headers", exc)
    else:
        _record_error(errors, "headers", ValueError("No headers were provided"), "missing_input")

    if normalized_subject.strip() or normalized_body.strip():
        social_score = _social_engineering_score(
            normalized_subject,
            normalized_body,
            config,
            detected_indicators,
        )
        _set_component(components["social_engineering"], social_score, {})
    else:
        _record_error(
            errors,
            "social_engineering",
            ValueError("No subject or body text was provided"),
            "missing_input",
        )

    available_weight = sum(
        component["weight"] for component in components.values() if component["available"]
    )
    if available_weight:
        for component in components.values():
            if component["available"]:
                component["contribution"] = round(
                    float(component["score"]) * component["weight"] / available_weight,
                    2,
                )
        final_score = sum(float(component["contribution"]) for component in components.values())
    else:
        final_score = 0.0
        detected_indicators.append(
            _indicator(
                "insufficient_data",
                "availability",
                "medium",
                "No risk components were available for scoring.",
                score=0,
            )
        )
    final_score = round(_bounded_score(final_score), 2)
    coverage = available_weight / sum(config.component_weights.values())
    confidence = round(_bounded_probability(abs(final_score - 50) / 50) * coverage, 2)
    classification = _classify(final_score, config.classification_thresholds)
    component_scores = {
        name: (
            round(float(component["score"]), 2)
            if component["available"]
            else None
        )
        for name, component in components.items()
    }
    available_components = [
        name for name, component in components.items() if component["available"]
    ]
    calculation = {
        "formula": (
            "sum(component_score * configured_weight) / "
            "sum(configured_weight for available components)"
        ),
        "configured_weights": {
            name: round(float(weight), 4)
            for name, weight in config.component_weights.items()
        },
        "available_components": available_components,
        "available_weight": round(available_weight, 4),
        "coverage": round(coverage, 4),
        "weighted_contributions": {
            name: component["contribution"] for name, component in components.items()
        },
        "thresholds": {
            threshold.label: threshold.maximum_score
            for threshold in config.classification_thresholds
        },
    }
    return {
        "score": final_score,
        "classification": classification,
        "confidence": confidence,
        "component_scores": component_scores,
        "components": components,
        "detected_indicators": detected_indicators,
        "calculation": calculation,
        "explanation": (
            f"Final score {final_score:.2f} is the normalized weighted average of "
            f"{', '.join(available_components) if available_components else 'no available components'}."
        ),
        "errors": errors,
    }


def analyze_risk(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility-friendly name for the central risk operation."""
    return assess_risk(*args, **kwargs)


def analyze_email_risk(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Descriptive alias for callers working with complete email records."""
    return assess_risk(*args, **kwargs)


def _set_component(component: dict[str, Any], score: float, details: dict[str, Any]) -> None:
    component["score"] = round(_bounded_score(score), 2)
    component["available"] = True
    component["details"] = details


def _text_prediction_score(prediction: Mapping[str, Any], config: RiskConfig) -> float:
    label = str(prediction.get("class", "")).strip().casefold()
    probability = _bounded_probability(prediction.get("probability", 0))
    if label in config.text_safe_labels:
        return (1 - probability) * 100
    return probability * 100 if label in config.text_risk_labels else probability * 100


def _url_prediction_score(prediction: Mapping[str, Any], config: RiskConfig) -> float:
    label = str(prediction.get("classification", "")).strip().casefold()
    probability = _bounded_probability(prediction.get("probability", 0))
    if label in config.url_safe_labels:
        return (1 - probability) * 100
    return probability * 100 if label in config.url_risk_labels else probability * 100


def _header_score(
    result: HeaderAnalysisResult | Mapping[str, Any],
    config: RiskConfig,
    indicators: list[dict[str, Any]],
) -> float:
    authentication = _value(result, "authentication", {})
    findings = _value(result, "findings", [])
    scores: list[float] = []
    for method, auth_result in authentication.items():
        state = _value(auth_result, "state", "UNKNOWN")
        state_value = getattr(state, "value", str(state)).upper()
        state_score = float(config.header_state_scores.get(state_value, 30))
        scores.append(state_score)
        if state_value in {"FAIL", "UNKNOWN"}:
            indicators.append(
                _indicator(
                    f"{str(method).lower()}_{state_value.lower()}",
                    "headers",
                    "high" if state_value == "FAIL" else "medium",
                    f"{method} authentication is reported as {state_value}.",
                    score=state_score,
                )
            )
    for finding in findings:
        code = str(_value(finding, "code", "header_finding"))
        severity = str(_value(finding, "severity", "medium"))
        finding_score = float(config.header_finding_scores.get(code, _severity_score(severity)))
        scores.append(finding_score)
        if finding_score > 0:
            indicators.append(
                _indicator(
                    code,
                    "headers",
                    severity,
                    str(_value(finding, "message", "Suspicious header finding detected.")),
                    score=finding_score,
                )
            )
    return min(max(scores, default=0), 100)


def _header_details(result: HeaderAnalysisResult | Mapping[str, Any]) -> dict[str, Any]:
    authentication = _value(result, "authentication", {})
    findings = _value(result, "findings", [])
    return {
        "authentication": {
            str(method): str(getattr(_value(auth, "state", "UNKNOWN"), "value", _value(auth, "state", "UNKNOWN")))
            for method, auth in authentication.items()
        },
        "finding_codes": [str(_value(finding, "code", "")) for finding in findings],
    }


def _domain_feature_score(
    url: str,
    features: Mapping[str, int],
    config: RiskConfig,
    indicators: list[dict[str, Any]],
) -> float:
    scores: list[float] = []
    for feature_name, feature_score in config.domain_feature_scores.items():
        if features.get(feature_name, 0):
            scores.append(float(feature_score))
    if not features.get("uses_https", 0):
        scores.append(config.domain_insecure_transport_score)
        indicators.append(
            _indicator(
                "insecure_transport",
                "domain_security",
                "low",
                "The URL uses HTTP instead of HTTPS.",
                score=config.domain_insecure_transport_score,
                url=url,
            )
        )
    if features.get("url_length", 0) >= config.domain_long_url_length:
        scores.append(config.domain_long_url_score)
        indicators.append(
            _indicator(
                "long_url",
                "domain_security",
                "low",
                "The URL is unusually long.",
                score=config.domain_long_url_score,
                url=url,
            )
        )
    if features.get("subdomain_count", 0) >= config.domain_subdomain_threshold:
        scores.append(config.domain_subdomain_score)
        indicators.append(
            _indicator(
                "many_subdomains",
                "domain_security",
                "low",
                "The URL contains several subdomain levels.",
                score=config.domain_subdomain_score,
                url=url,
            )
        )
    for feature_name, feature_score in config.domain_feature_scores.items():
        if features.get(feature_name, 0):
            indicators.append(
                _indicator(
                    feature_name,
                    "domain_security",
                    "high" if feature_score >= 70 else "medium",
                    f"The URL has the static security feature {feature_name}.",
                    score=feature_score,
                    url=url,
                )
            )
    return min(max(scores, default=0), 100)


def _social_engineering_score(
    subject: str,
    body: str,
    config: RiskConfig,
    indicators: list[dict[str, Any]],
) -> float:
    text = f"{subject}\n{body}"
    total = 0.0
    for rule in config.social_rules:
        matches = [match.group(0).strip() for match in re.finditer(rule.pattern, text, re.IGNORECASE)]
        if not matches:
            continue
        total += rule.score
        indicators.append(
            _indicator(
                rule.code,
                "social_engineering",
                rule.severity,
                rule.message,
                score=rule.score,
                matched_terms=sorted(set(matches), key=str.casefold),
            )
        )
    return min(total, 100)


def _normalize_urls(urls: Sequence[str] | None, errors: list[dict[str, str]]) -> list[str]:
    if urls is None:
        return []
    if isinstance(urls, str):
        return [urls]
    try:
        return [str(url).strip() for url in urls if str(url).strip()]
    except TypeError as exc:
        _record_error(errors, "url", exc, "invalid_input")
        return []


def _classify(score: float, thresholds: Sequence[ClassificationThreshold]) -> str:
    for threshold in thresholds:
        if score <= threshold.maximum_score:
            return threshold.label
    return thresholds[-1].label


def _indicator(
    code: str,
    category: str,
    severity: str,
    message: str,
    *,
    score: float,
    **details: Any,
) -> dict[str, Any]:
    return {
        "code": code,
        "category": category,
        "severity": severity,
        "message": message,
        "score": round(_bounded_score(score), 2),
        "details": details,
    }


def _record_error(
    errors: list[dict[str, str]],
    component: str,
    exc: Exception,
    code: str | None = None,
    **details: str,
) -> None:
    error: dict[str, str] = {
        "component": component,
        "code": code or "component_unavailable",
        "message": _safe_error_message(exc),
    }
    error.update(details)
    errors.append(error)


def _safe_error_message(exc: Exception) -> str:
    """Return a diagnostic-safe message without paths, input, or stack details."""
    del exc
    return "Component analysis unavailable."


def _value(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _coerce_text(value: str | None) -> str:
    return "" if value is None else str(value)


def _bounded_probability(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(max(number, 0.0), 1.0) if math.isfinite(number) else 0.0


def _bounded_score(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(max(number, 0.0), 100.0) if math.isfinite(number) else 0.0


def _severity_score(severity: str) -> float:
    return {"critical": 90.0, "high": 75.0, "medium": 50.0, "low": 25.0}.get(
        severity.casefold(),
        50.0,
    )
