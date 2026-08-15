"""SQLAlchemy models for the PhishZero database layer."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for ORM defaults."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Shared audit timestamps for database records."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(email) >= 3", name="ck_users_email_length"),
        CheckConstraint(
            "length(password_hash) >= 20",
            name="ck_users_password_hash_length",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    emails: Mapped[list[Email]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    feedback: Mapped[list[AnalysisFeedback]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Email(TimestampMixin, Base):
    __tablename__ = "emails"
    __table_args__ = (
        Index("ix_emails_user_received_at", "user_id", "received_at"),
        CheckConstraint("length(sender) >= 3", name="ck_emails_sender_length"),
        CheckConstraint("length(recipient) >= 3", name="ck_emails_recipient_length"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    message_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    sender: Mapped[str] = mapped_column(String(320), nullable=False)
    recipient: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(998), nullable=True)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    html_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_headers: Mapped[list[dict[str, str]]] = mapped_column(
        JSON,
        default=list,
        server_default=text("'[]'"),
        nullable=False,
    )
    extracted_urls: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        server_default=text("'[]'"),
        nullable=False,
    )
    attachment_metadata: Mapped[list[dict[str, object]]] = mapped_column(
        JSON,
        default=list,
        server_default=text("'[]'"),
        nullable=False,
    )
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="emails")
    analyses: Mapped[list[Analysis]] = relationship(
        back_populates="email",
        cascade="all, delete-orphan",
    )


class Analysis(TimestampMixin, Base):
    __tablename__ = "analyses"
    __table_args__ = (
        CheckConstraint(
            "verdict IN ('pending', 'safe', 'spam', 'phishing', 'suspicious')",
            name="ck_analyses_verdict",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_analyses_confidence_range",
        ),
        CheckConstraint(
            "risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100)",
            name="ck_analyses_risk_score_range",
        ),
        CheckConstraint(
            "classification IN ('SAFE', 'LOW_RISK', 'SUSPICIOUS', 'PHISHING')",
            name="ck_analyses_classification",
        ),
        Index("ix_analyses_email_created_at", "email_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email_id: Mapped[int] = mapped_column(
        ForeignKey("emails.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    verdict: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="SAFE", nullable=False)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    component_scores: Mapped[dict[str, object]] = mapped_column(
        JSON,
        default=dict,
        server_default=text("'{}'"),
        nullable=False,
    )
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    email: Mapped[Email] = relationship(back_populates="analyses")
    urls: Mapped[list[URL]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    threat_indicators: Mapped[list[ThreatIndicator]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    feedback: Mapped[list[AnalysisFeedback]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
    )


class URL(TimestampMixin, Base):
    __tablename__ = "urls"
    __table_args__ = (
        UniqueConstraint("analysis_id", "url", name="uq_urls_analysis_url"),
        CheckConstraint(
            "verdict IN ('pending', 'safe', 'malicious', 'suspicious')",
            name="ck_urls_verdict",
        ),
        CheckConstraint(
            "risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 1)",
            name="ck_urls_risk_score_range",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(253), nullable=True, index=True)
    verdict: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)

    analysis: Mapped[Analysis] = relationship(back_populates="urls")


class ThreatIndicator(TimestampMixin, Base):
    __tablename__ = "threat_indicators"
    __table_args__ = (
        UniqueConstraint(
            "analysis_id",
            "indicator_type",
            "value",
            name="uq_threat_indicators_analysis_type_value",
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="ck_threat_indicators_severity",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    indicator_type: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str] = mapped_column(String(512), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis: Mapped[Analysis] = relationship(back_populates="threat_indicators")


class AnalysisFeedback(TimestampMixin, Base):
    __tablename__ = "analysis_feedback"
    __table_args__ = (
        UniqueConstraint("user_id", "analysis_id", name="uq_analysis_feedback_user_analysis"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="feedback")
    analysis: Mapped[Analysis] = relationship(back_populates="feedback")
