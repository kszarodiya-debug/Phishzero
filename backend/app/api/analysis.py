"""Authenticated email analysis endpoints."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.database import get_db
from app.db.models import Analysis, Email, ThreatIndicator, URL
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, ThreatResponse
from app.services.email_parser import ParsedEmail, parse_manual_email
from app.services.explanation_engine import ExplanationResult, generate_explanation
from app.services.risk_engine import assess_risk


router = APIRouter(prefix="/api/analysis", tags=["analysis"])
RISK_ENGINE_VERSION = "risk-engine-v1"
ALLOWED_THREAT_SEVERITIES = {"low", "medium", "high", "critical"}


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
def create_analysis(
    payload: AnalysisRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    """Parse, analyze, and persist one email for the authenticated user."""
    parsed_email = parse_manual_email(payload)
    risk_result = assess_risk(
        subject=parsed_email.subject,
        body=parsed_email.body_text,
        urls=parsed_email.urls,
        headers=parsed_email.raw_headers,
    )
    explanation_result = generate_explanation(risk_result)

    stored_email = Email(
        user_id=current_user.id,
        sender=parsed_email.sender,
        recipient=", ".join(parsed_email.recipients),
        subject=parsed_email.subject,
        body_text=parsed_email.body_text,
        html_body=parsed_email.html_body,
        raw_headers=[header.model_dump() for header in parsed_email.raw_headers],
        extracted_urls=parsed_email.urls,
        attachment_metadata=[attachment.model_dump() for attachment in parsed_email.attachments],
    )
    db.add(stored_email)
    db.flush()

    analysis = Analysis(
        email_id=stored_email.id,
        classification=_classification_value(risk_result),
        verdict=_verdict_for_classification(str(risk_result.get("classification", "SAFE"))),
        risk_score=_decimal_or_zero(risk_result.get("score"), maximum=100),
        confidence=_decimal_or_zero(risk_result.get("confidence"), maximum=1),
        component_scores=_component_scores(risk_result),
        model_version=_model_version(risk_result),
        explanation=_explanation(risk_result, explanation_result),
        analyzed_at=datetime.now(timezone.utc),
    )
    db.add(analysis)
    db.flush()

    _persist_urls(db, analysis, parsed_email.urls, risk_result)
    _persist_threats(db, analysis, risk_result)

    db.commit()
    db.refresh(analysis)
    return _to_response(analysis, risk_result)


@router.get("/history", response_model=list[AnalysisResponse])
def analysis_history(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[AnalysisResponse]:
    """Return only analyses belonging to the authenticated user."""
    analyses = db.scalars(
        select(Analysis)
        .join(Email, Analysis.email_id == Email.id)
        .where(Email.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [_to_response(analysis, _stored_result(analysis)) for analysis in analyses]


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    """Return one owned analysis without revealing whether other users have it."""
    analysis = db.scalar(
        select(Analysis)
        .join(Email, Analysis.email_id == Email.id)
        .where(
            Analysis.id == analysis_id,
            Email.user_id == current_user.id,
        )
    )
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )
    return _to_response(analysis, _stored_result(analysis))


def _persist_urls(
    db: Session,
    analysis: Analysis,
    urls: list[str],
    risk_result: dict[str, Any],
) -> None:
    predictions = _url_predictions(risk_result)
    for url in urls:
        prediction = predictions.get(url, {})
        classification = str(prediction.get("classification", "")).casefold()
        stored_url = URL(
            analysis_id=analysis.id,
            url=url,
            domain=_url_domain(url),
            verdict=_url_verdict(classification),
            risk_score=_decimal_or_none(
                _numeric(prediction.get("score")),
                maximum=100,
                divisor=100,
            ),
        )
        db.add(stored_url)


def _persist_threats(db: Session, analysis: Analysis, risk_result: dict[str, Any]) -> None:
    seen: set[tuple[str, str]] = set()
    for indicator in risk_result.get("detected_indicators", []):
        if not isinstance(indicator, dict):
            continue
        indicator_type = str(indicator.get("code", "risk_indicator")).strip()[:64]
        details = indicator.get("details")
        details = details if isinstance(details, dict) else {}
        value = str(details.get("url") or indicator_type).strip()[:512]
        key = (indicator_type, value)
        if not indicator_type or key in seen:
            continue
        seen.add(key)
        severity = str(indicator.get("severity", "medium")).casefold()
        if severity not in ALLOWED_THREAT_SEVERITIES:
            severity = "low" if severity == "info" else "medium"
        db.add(
            ThreatIndicator(
                analysis_id=analysis.id,
                indicator_type=indicator_type,
                value=value,
                severity=severity,
                source=str(indicator.get("category", "risk_engine"))[:128],
                description=str(indicator.get("message", "Risk indicator detected"))[:10_000],
            )
        )


def _to_response(analysis: Analysis, risk_result: dict[str, Any]) -> AnalysisResponse:
    component_scores = risk_result.get("component_scores", {})
    urls = [stored_url.url for stored_url in analysis.urls]
    threats = [
        ThreatResponse(
            indicator_type=threat.indicator_type,
            value=threat.value,
            severity=threat.severity,
            source=threat.source,
            description=threat.description,
        )
        for threat in analysis.threat_indicators
    ]
    classification = str(risk_result.get("classification", "SAFE")).upper()
    if classification not in {"SAFE", "LOW_RISK", "SUSPICIOUS", "PHISHING"}:
        classification = "SAFE"
    explanation = _stored_explanation(analysis)
    return AnalysisResponse(
        analysis_id=analysis.id,
        classification=classification,
        risk_score=float(analysis.risk_score or 0),
        confidence=float(analysis.confidence or 0),
        text_score=_component_score(component_scores, "text"),
        url_score=_component_score(component_scores, "url"),
        header_score=_component_score(component_scores, "headers"),
        threats=threats,
        analyzed_urls=urls,
        model_version=analysis.model_version or RISK_ENGINE_VERSION,
        summary=explanation["summary"],
        reasons=explanation["reasons"],
        recommended_actions=explanation["recommended_actions"],
        created_at=analysis.created_at,
    )


def _stored_result(analysis: Analysis) -> dict[str, Any]:
    """Build the stable response fields available from persisted records."""
    return {
        "classification": analysis.classification or _classification_for_verdict(analysis.verdict),
        "component_scores": analysis.component_scores or {},
    }


def _classification_for_verdict(verdict: str) -> str:
    return {
        "safe": "SAFE",
        "spam": "LOW_RISK",
        "suspicious": "SUSPICIOUS",
        "phishing": "PHISHING",
    }.get(verdict, "SAFE")


def _classification_value(risk_result: dict[str, Any]) -> str:
    classification = str(risk_result.get("classification", "SAFE")).upper()
    return classification if classification in {"SAFE", "LOW_RISK", "SUSPICIOUS", "PHISHING"} else "SAFE"


def _component_score(component_scores: Any, name: str) -> float | None:
    if not isinstance(component_scores, dict):
        return None
    value = component_scores.get(name)
    return float(value) if isinstance(value, (int, float)) else None


def _component_scores(risk_result: dict[str, Any]) -> dict[str, float | None]:
    component_scores = risk_result.get("component_scores", {})
    if not isinstance(component_scores, dict):
        return {}
    return {
        str(name): float(value) if isinstance(value, (int, float)) else None
        for name, value in component_scores.items()
    }


def _url_predictions(risk_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    components = risk_result.get("components", {})
    url_component = components.get("url", {}) if isinstance(components, dict) else {}
    details = url_component.get("details", {}) if isinstance(url_component, dict) else {}
    predictions = details.get("predictions", []) if isinstance(details, dict) else []
    return {
        str(prediction.get("url")): prediction
        for prediction in predictions
        if isinstance(prediction, dict) and prediction.get("url")
    }


def _model_version(risk_result: dict[str, Any]) -> str:
    explicit_version = risk_result.get("model_version")
    if explicit_version:
        return str(explicit_version)[:64]
    components = risk_result.get("components", {})
    text_component = components.get("text", {}) if isinstance(components, dict) else {}
    details = text_component.get("details", {}) if isinstance(text_component, dict) else {}
    text_version = details.get("model_version") if isinstance(details, dict) else None
    if text_version:
        return str(text_version)[:64]
    return RISK_ENGINE_VERSION


def _explanation(risk_result: dict[str, Any], explanation_result: ExplanationResult) -> str:
    payload = explanation_result.model_dump()
    payload["risk_engine_explanation"] = str(
        risk_result.get("explanation", "Risk engine analysis completed.")
    )
    calculation = risk_result.get("calculation")
    if isinstance(calculation, dict):
        payload["calculation"] = calculation
    return json.dumps(payload, sort_keys=True)


def _stored_explanation(analysis: Analysis) -> dict[str, Any]:
    fallback = {
        "summary": "No specific suspicious evidence was produced by the available analyzers.",
        "reasons": [],
        "recommended_actions": [],
    }
    if not analysis.explanation:
        return fallback
    try:
        stored = json.loads(analysis.explanation)
    except (TypeError, ValueError):
        return {**fallback, "summary": str(analysis.explanation)}
    if not isinstance(stored, dict):
        return fallback
    reasons = stored.get("reasons", [])
    actions = stored.get("recommended_actions", [])
    return {
        "summary": str(stored.get("summary", fallback["summary"])),
        "reasons": [str(reason) for reason in reasons] if isinstance(reasons, list) else [],
        "recommended_actions": [str(action) for action in actions] if isinstance(actions, list) else [],
    }


def _verdict_for_classification(classification: str) -> str:
    return {
        "SAFE": "safe",
        "LOW_RISK": "safe",
        "SUSPICIOUS": "suspicious",
        "PHISHING": "phishing",
    }.get(classification.upper(), "pending")


def _url_verdict(classification: str) -> str:
    return {
        "benign": "safe",
        "safe": "safe",
        "legitimate": "safe",
        "phishing": "malicious",
        "malicious": "malicious",
        "suspicious": "suspicious",
    }.get(classification, "pending")


def _url_domain(url: str) -> str | None:
    try:
        return (urlsplit(url).hostname or "").lower().rstrip(".") or None
    except ValueError:
        return None


def _numeric(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def _decimal_or_zero(value: Any, *, maximum: float) -> Decimal:
    numeric = _numeric(value)
    if numeric is None:
        numeric = 0
    return Decimal(str(min(max(numeric, 0), maximum)))


def _decimal_or_none(value: Any, *, maximum: float, divisor: float = 1) -> Decimal | None:
    numeric = _numeric(value)
    if numeric is None:
        return None
    return Decimal(str(min(max(numeric / divisor, 0), maximum / divisor)))
