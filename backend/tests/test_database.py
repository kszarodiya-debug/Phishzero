from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import Analysis, AnalysisFeedback, Email, ThreatIndicator, URL, User


@pytest.fixture()
def session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db
    Base.metadata.drop_all(engine)
    engine.dispose()


def make_graph(session: Session) -> tuple[User, Email, Analysis]:
    user = User(
        email="analyst@example.com",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$test-hash-value",
        display_name="Analyst",
    )
    email = Email(
        user=user,
        sender="sender@example.com",
        recipient="analyst@example.com",
        subject="Review this message",
        body_text="Message body for authorized defensive analysis.",
        received_at=datetime.now(timezone.utc),
    )
    analysis = Analysis(
        email=email,
        verdict="phishing",
        confidence=Decimal("0.9800"),
        model_version="foundation",
    )
    analysis.urls.append(
        URL(
            url="https://example.com/account",
            domain="example.com",
            verdict="suspicious",
            risk_score=Decimal("0.8500"),
        )
    )
    analysis.threat_indicators.append(
        ThreatIndicator(
            indicator_type="sender_domain",
            value="example.com",
            severity="medium",
            source="local-analysis",
        )
    )
    analysis.feedback.append(
        AnalysisFeedback(
            user=user,
            is_correct=True,
            comment="Confirmed during authorized review.",
        )
    )
    session.add(user)
    session.commit()
    return user, email, analysis


def test_all_tables_are_declared(session: Session) -> None:
    table_names = set(inspect(session.bind).get_table_names())
    assert table_names == {
        "users",
        "emails",
        "analyses",
        "urls",
        "threat_indicators",
        "analysis_feedback",
    }


def test_relationships_and_timestamps_are_persisted(session: Session) -> None:
    user, email, analysis = make_graph(session)

    assert user.id is not None
    assert email in user.emails
    assert analysis in email.analyses
    assert len(analysis.urls) == 1
    assert len(analysis.threat_indicators) == 1
    assert len(analysis.feedback) == 1
    assert isinstance(user.created_at, datetime)
    assert isinstance(analysis.updated_at, datetime)


def test_password_plaintext_column_does_not_exist() -> None:
    assert "password" not in User.__table__.columns
    assert "password_hash" in User.__table__.columns


def test_constraints_reject_duplicate_user_and_invalid_confidence(session: Session) -> None:
    make_graph(session)
    duplicate = User(
        email="analyst@example.com",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$another-hash-value",
    )
    session.add(duplicate)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    user = session.query(User).one()
    invalid_email = Email(
        user=user,
        sender="sender@example.com",
        recipient="analyst@example.com",
        body_text="Invalid analysis fixture.",
    )
    invalid_analysis = Analysis(email=invalid_email, verdict="phishing", confidence=Decimal("1.1000"))
    session.add(invalid_analysis)
    with pytest.raises(IntegrityError):
        session.commit()


def test_cascade_relationships_remove_dependent_records(session: Session) -> None:
    user, _, _ = make_graph(session)
    user_id = user.id
    session.delete(user)
    session.commit()

    assert session.query(User).filter_by(id=user_id).one_or_none() is None
    assert session.query(Email).count() == 0
    assert session.query(Analysis).count() == 0
    assert session.query(URL).count() == 0
    assert session.query(ThreatIndicator).count() == 0
    assert session.query(AnalysisFeedback).count() == 0
