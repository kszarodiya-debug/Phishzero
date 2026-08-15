"""Request and response schemas for authenticated email analysis."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.email import ManualEmailInput


class AnalysisRequest(ManualEmailInput):
    """Validated manual email input reused by the analysis endpoint."""


class ThreatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    indicator_type: str
    value: str
    severity: str
    source: str | None
    description: str | None


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    analysis_id: int
    classification: Literal["SAFE", "LOW_RISK", "SUSPICIOUS", "PHISHING"]
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    text_score: float | None = Field(default=None, ge=0, le=100)
    url_score: float | None = Field(default=None, ge=0, le=100)
    header_score: float | None = Field(default=None, ge=0, le=100)
    threats: list[ThreatResponse]
    analyzed_urls: list[str]
    model_version: str
    summary: str
    reasons: list[str]
    recommended_actions: list[str]
    created_at: datetime
