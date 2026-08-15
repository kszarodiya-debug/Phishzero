"""Anonymous, non-persistent email verification endpoint."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, status

from app.schemas.public_analysis import (
    PublicAnalysisRequest,
    PublicAnalysisResponse,
    PublicThreatResponse,
)
from app.services.email_parser import parse_manual_email
from app.services.explanation_engine import generate_explanation
from app.services.risk_engine import assess_risk
from app.services.security_type import security_type_for


router = APIRouter(prefix="/api/public", tags=["public-analysis"])
RISK_ENGINE_VERSION = "risk-engine-v1"
ALLOWED_CLASSIFICATIONS = {"SAFE", "LOW_RISK", "SUSPICIOUS", "PHISHING"}


@router.post("/analysis", response_model=PublicAnalysisResponse, status_code=status.HTTP_200_OK)
def verify_email(payload: PublicAnalysisRequest) -> PublicAnalysisResponse:
    """Analyze one email without authentication and without persisting its content."""
    parsed_email = parse_manual_email(payload)
    risk_result = assess_risk(
        subject=parsed_email.subject,
        body=parsed_email.body_text,
        urls=parsed_email.urls,
        headers=parsed_email.raw_headers,
    )
    explanation = generate_explanation(risk_result)
    component_scores = risk_result.get("component_scores", {})
    classification = str(risk_result.get("classification", "SAFE")).upper()
    if classification not in ALLOWED_CLASSIFICATIONS:
        classification = "SAFE"

    return PublicAnalysisResponse(
        classification=classification,
        security_type=security_type_for(classification),
        risk_score=_number(risk_result.get("score"), maximum=100),
        confidence=_number(risk_result.get("confidence"), maximum=1),
        text_score=_component_score(component_scores, "text"),
        url_score=_component_score(component_scores, "url"),
        header_score=_component_score(component_scores, "headers"),
        threats=_threats(risk_result.get("detected_indicators")),
        analyzed_urls=parsed_email.urls,
        model_version=_model_version(risk_result),
        summary=explanation.summary,
        reasons=explanation.reasons,
        recommended_actions=explanation.recommended_actions,
    )


def _component_score(component_scores: Any, name: str) -> float | None:
    if not isinstance(component_scores, Mapping):
        return None
    value = component_scores.get(name)
    return _number(value, maximum=100) if isinstance(value, (int, float)) else None


def _threats(indicators: Any) -> list[PublicThreatResponse]:
    if not isinstance(indicators, list):
        return []
    threats: list[PublicThreatResponse] = []
    seen: set[tuple[str, str]] = set()
    for indicator in indicators:
        if not isinstance(indicator, Mapping):
            continue
        indicator_type = str(indicator.get("code", "risk_indicator")).strip()[:64]
        details = indicator.get("details")
        details = details if isinstance(details, Mapping) else {}
        value = str(details.get("url") or indicator_type).strip()[:512]
        key = (indicator_type, value)
        if not indicator_type or key in seen:
            continue
        seen.add(key)
        threats.append(
            PublicThreatResponse(
                indicator_type=indicator_type,
                value=value,
                severity=str(indicator.get("severity", "medium"))[:32],
                source=str(indicator.get("category", "risk_engine"))[:128],
                description=str(indicator.get("message", "Risk indicator detected"))[:10_000],
            )
        )
    return threats


def _model_version(risk_result: Mapping[str, Any]) -> str:
    explicit_version = risk_result.get("model_version")
    if explicit_version:
        return str(explicit_version)[:64]
    components = risk_result.get("components", {})
    text_component = components.get("text", {}) if isinstance(components, Mapping) else {}
    details = text_component.get("details", {}) if isinstance(text_component, Mapping) else {}
    text_version = details.get("model_version") if isinstance(details, Mapping) else None
    return str(text_version)[:64] if text_version else RISK_ENGINE_VERSION


def _number(value: Any, *, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(max(number, 0.0), maximum)

