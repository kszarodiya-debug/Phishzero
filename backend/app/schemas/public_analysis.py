"""Schemas for the non-persistent public email verification endpoint."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.email import ManualEmailInput
from app.services.security_type import SecurityType


class PublicAnalysisRequest(ManualEmailInput):
    """Validated email data accepted for an anonymous, non-persistent check."""


class PublicThreatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    indicator_type: str
    value: str
    severity: str
    source: str | None
    description: str | None


class PublicAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification: Literal["SAFE", "LOW_RISK", "SUSPICIOUS", "PHISHING"]
    security_type: SecurityType
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    text_score: float | None = Field(default=None, ge=0, le=100)
    url_score: float | None = Field(default=None, ge=0, le=100)
    header_score: float | None = Field(default=None, ge=0, le=100)
    threats: list[PublicThreatResponse]
    analyzed_urls: list[str]
    model_version: str
    summary: str
    reasons: list[str]
    recommended_actions: list[str]

