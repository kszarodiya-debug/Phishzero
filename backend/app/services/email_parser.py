"""Safe manual and raw .eml parsing helpers.

This module only parses message bytes and metadata. It never writes, opens,
executes, or otherwise processes attachment contents, and it never performs
network requests for extracted URLs.
"""

from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.header import decode_header, make_header
from email.parser import BytesParser
from email.utils import getaddresses, parseaddr
import re
from urllib.parse import unquote, urlsplit

from pydantic import EmailStr, TypeAdapter, ValidationError

from app.schemas.email import AttachmentMetadata, ManualEmailInput, RawHeader


MAX_EMAIL_BYTES = 5 * 1024 * 1024
MAX_ATTACHMENT_METADATA = 100
_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_TRAILING_URL_CHARACTERS = ".,;:!?)]}>\"'"
_EMAIL_ADDRESS_ADAPTER = TypeAdapter(EmailStr)


class EmailParseError(ValueError):
    """Raised when an email cannot be safely parsed or validated."""


@dataclass(frozen=True)
class ParsedEmail:
    sender: str
    recipients: list[str]
    subject: str | None
    body_text: str
    html_body: str | None
    raw_headers: list[RawHeader]
    urls: list[str]
    attachments: list[AttachmentMetadata]


def parse_manual_email(email: ManualEmailInput) -> ParsedEmail:
    """Validate and normalize manually supplied email fields."""
    html_body = email.html_body or None
    return ParsedEmail(
        sender=str(email.sender),
        recipients=[str(recipient) for recipient in email.recipients],
        subject=email.subject,
        body_text=email.body_text,
        html_body=html_body,
        raw_headers=list(email.raw_headers),
        urls=extract_urls("\n".join((email.body_text, html_body or ""))),
        attachments=[],
    )


def parse_eml(raw_message: bytes) -> ParsedEmail:
    """Parse a raw RFC 5322 message without executing any message content."""
    if not raw_message:
        raise EmailParseError("The .eml file is empty")
    if len(raw_message) > MAX_EMAIL_BYTES:
        raise EmailParseError("The .eml file exceeds the maximum size")

    try:
        message = BytesParser(policy=policy.default).parsebytes(raw_message)
        sender = _extract_sender(message.get("From"))
        recipients = _extract_recipients(
            message.get_all("To", [])
            + message.get_all("Cc", [])
            + message.get_all("Bcc", [])
        )
        if not sender or not recipients:
            raise EmailParseError("The .eml file must contain a valid From and recipient header")
        try:
            sender = str(_EMAIL_ADDRESS_ADAPTER.validate_python(sender))
            recipients = [str(_EMAIL_ADDRESS_ADAPTER.validate_python(recipient)) for recipient in recipients]
        except ValidationError as exc:
            raise EmailParseError("The .eml file contains an invalid email address") from exc

        body_text, html_body = _extract_bodies(message)
        attachments = _extract_attachment_metadata(message)
        raw_headers = [
            RawHeader(name=name, value=_normalize_header_value(value))
            for name, value in message.raw_items()
        ]
        return ParsedEmail(
            sender=sender,
            recipients=recipients,
            subject=_decode_header_value(message.get("Subject")) if message.get("Subject") else None,
            body_text=body_text,
            html_body=html_body,
            raw_headers=raw_headers,
            urls=extract_urls("\n".join((body_text, html_body or ""))),
            attachments=attachments,
        )
    except EmailParseError:
        raise
    except (LookupError, TypeError, ValueError) as exc:
        raise EmailParseError("The .eml file could not be parsed safely") from exc


def extract_urls(text: str) -> list[str]:
    """Extract unique HTTP(S) URLs without resolving or visiting them."""
    urls: list[str] = []
    seen: set[str] = set()
    for match in _URL_PATTERN.findall(text):
        candidate = unquote(match).rstrip(_TRAILING_URL_CHARACTERS)
        parsed = urlsplit(candidate)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            continue
        if candidate not in seen:
            seen.add(candidate)
            urls.append(candidate)
    return urls


def _extract_sender(value: str | None) -> str | None:
    if not value:
        return None
    _, address = parseaddr(value)
    return address.strip() or None


def _extract_recipients(values: list[str]) -> list[str]:
    recipients: list[str] = []
    seen: set[str] = set()
    for _, address in getaddresses(values):
        normalized = address.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            recipients.append(normalized)
    return recipients


def _extract_bodies(message) -> tuple[str, str | None]:
    plain_parts: list[str] = []
    html_parts: list[str] = []
    for part in message.walk():
        if part.is_multipart():
            continue
        filename = part.get_filename()
        disposition = (part.get_content_disposition() or "").lower()
        if filename or disposition == "attachment":
            continue
        content_type = part.get_content_type().lower()
        if content_type not in {"text/plain", "text/html"}:
            continue
        content = _decode_text_part(part)
        if content_type == "text/plain":
            plain_parts.append(content)
        else:
            html_parts.append(content)
    return "\n".join(part for part in plain_parts if part), "\n".join(html_parts) or None


def _decode_text_part(part) -> str:
    try:
        return part.get_content()
    except (LookupError, TypeError, UnicodeError):
        payload = part.get_payload(decode=True)
        if payload is None:
            raw_payload = part.get_payload(decode=False)
            return raw_payload if isinstance(raw_payload, str) else ""
        charset = part.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")


def _extract_attachment_metadata(message) -> list[AttachmentMetadata]:
    attachments: list[AttachmentMetadata] = []
    for part in message.walk():
        if part.is_multipart():
            continue
        filename = part.get_filename()
        disposition = part.get_content_disposition()
        if not filename and disposition != "attachment":
            continue

        # Decoding stays in memory solely to measure the payload; it is never
        # written to disk, opened as a file, or passed to an executable.
        decoded_payload = part.get_payload(decode=True)
        attachments.append(
            AttachmentMetadata(
                filename=filename,
                content_type=part.get_content_type(),
                size_bytes=len(decoded_payload) if decoded_payload is not None else None,
                content_disposition=disposition,
            )
        )
        if len(attachments) >= MAX_ATTACHMENT_METADATA:
            break
    return attachments


def _decode_header_value(value: str) -> str:
    try:
        return str(make_header(decode_header(value)))
    except (LookupError, TypeError, UnicodeError):
        return value


def _normalize_header_value(value: str) -> str:
    """Unfold valid MIME continuations before storing a header value."""
    decoded = _decode_header_value(value)
    return re.sub(r"\r?\n[ \t]+", " ", decoded).replace("\r", " ").replace("\n", " ").strip()
