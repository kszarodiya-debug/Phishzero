from email.message import EmailMessage

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app
from app.services.email_parser import MAX_EMAIL_BYTES, EmailParseError, parse_eml


TEST_SECRET = "test-only-email-secret-key-that-is-at-least-32-characters"


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def auth_headers(client: TestClient) -> dict[str, str]:
    registration = client.post(
        "/api/auth/register",
        json={
            "email": "ingestion@example.com",
            "password": "SecurePass123!",
        },
    )
    assert registration.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={
            "email": "ingestion@example.com",
            "password": "SecurePass123!",
        },
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_plain_text_email() -> None:
    raw_message = (
        b"From: sender@example.com\r\n"
        b"To: analyst@example.com\r\n"
        b"Subject: Plain message\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"This is the plain-text body.\r\n"
    )

    parsed = parse_eml(raw_message)

    assert parsed.sender == "sender@example.com"
    assert parsed.recipients == ["analyst@example.com"]
    assert parsed.subject == "Plain message"
    assert "This is the plain-text body." in parsed.body_text
    assert parsed.html_body is None


def test_html_email() -> None:
    message = EmailMessage()
    message["From"] = "sender@example.com"
    message["To"] = "analyst@example.com"
    message["Subject"] = "HTML message"
    message.set_content("Plain fallback")
    message.add_alternative(
        '<html><body><p>HTML body</p><a href="https://example.com/path">Link</a></body></html>',
        subtype="html",
    )

    parsed = parse_eml(message.as_bytes())

    assert parsed.html_body is not None
    assert "HTML body" in parsed.html_body
    assert "https://example.com/path" in parsed.urls


def test_malformed_email() -> None:
    with pytest.raises(EmailParseError):
        parse_eml(b"This is not a valid message with sender and recipient headers")


def test_multiple_recipients() -> None:
    raw_message = (
        b"From: sender@example.com\r\n"
        b"To: first@example.com, Second <second@example.com>\r\n"
        b"Cc: third@example.com\r\n"
        b"Subject: Multiple recipients\r\n"
        b"\r\n"
        b"Body\r\n"
    )

    parsed = parse_eml(raw_message)

    assert parsed.recipients == [
        "first@example.com",
        "second@example.com",
        "third@example.com",
    ]


def test_multiple_urls() -> None:
    raw_message = (
        b"From: sender@example.com\r\n"
        b"To: analyst@example.com\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Visit https://one.example/path and http://two.example/?q=1.\r\n"
    )

    parsed = parse_eml(raw_message)

    assert parsed.urls == [
        "https://one.example/path",
        "http://two.example/?q=1",
    ]


def test_attachment_metadata() -> None:
    message = EmailMessage()
    message["From"] = "sender@example.com"
    message["To"] = "analyst@example.com"
    message["Subject"] = "Attachment metadata"
    message.set_content("Message with metadata only")
    message.add_attachment(b"safe-bytes", maintype="text", subtype="plain", filename="notes.txt")

    parsed = parse_eml(message.as_bytes())

    assert len(parsed.attachments) == 1
    assert parsed.attachments[0].filename == "notes.txt"
    assert parsed.attachments[0].content_type == "text/plain"
    assert parsed.attachments[0].size_bytes == len(b"safe-bytes")


def test_manual_email_is_stored_for_authenticated_user(client: TestClient) -> None:
    headers = auth_headers(client)
    response = client.post(
        "/api/emails",
        headers=headers,
        json={
            "sender": "sender@example.com",
            "recipients": ["one@example.com", "two@example.com"],
            "subject": "Manual email",
            "body_text": "Manual body with https://example.com/a.",
            "html_body": "<p>Manual HTML</p>",
            "raw_headers": [{"name": "X-Source", "value": "manual"}],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["recipients"] == ["one@example.com", "two@example.com"]
    assert body["urls"] == ["https://example.com/a"]
    assert body["attachments"] == []


def test_raw_eml_is_stored_for_authenticated_user(client: TestClient) -> None:
    headers = auth_headers(client)
    message = EmailMessage()
    message["From"] = "sender@example.com"
    message["To"] = "analyst@example.com"
    message["Subject"] = "Uploaded email"
    message.set_content("Uploaded body")
    raw_message = message.as_bytes()

    response = client.post(
        "/api/emails",
        headers=headers,
        files={"file": ("uploaded.eml", raw_message, "message/rfc822")},
    )

    assert response.status_code == 201
    assert response.json()["subject"] == "Uploaded email"
    assert response.json()["body_text"] == "Uploaded body\n"


def test_rejects_non_eml_upload(client: TestClient) -> None:
    response = client.post(
        "/api/emails",
        headers=auth_headers(client),
        files={"file": ("not-an-email.txt", b"not an email", "text/plain")},
    )

    assert response.status_code == 415


def test_rejects_oversized_raw_email(client: TestClient) -> None:
    oversized_message = b"From: sender@example.com\r\n" + b"x" * (MAX_EMAIL_BYTES + 1)
    headers = auth_headers(client)
    headers["Content-Type"] = "message/rfc822"
    response = client.post(
        "/api/emails",
        headers=headers,
        content=oversized_message,
    )

    assert response.status_code == 413
