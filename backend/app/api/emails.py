"""Authenticated email ingestion endpoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import PurePosixPath, PureWindowsPath

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.api.dependencies import CurrentUser
from app.db.database import get_db
from app.db.models import Email
from app.schemas.email import ManualEmailInput, ParsedEmailResponse
from app.services.email_parser import (
    MAX_EMAIL_BYTES,
    EmailParseError,
    ParsedEmail,
    parse_eml,
    parse_manual_email,
)


router = APIRouter(prefix="/api/emails", tags=["emails"])
ALLOWED_EML_CONTENT_TYPES = {
    "application/eml",
    "application/octet-stream",
    "message/rfc822",
    "text/plain",
}


@router.post("", response_model=ParsedEmailResponse, status_code=status.HTTP_201_CREATED)
async def ingest_email(
    request: Request,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ParsedEmailResponse:
    parsed_email = await _parse_request(request)
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
    db.commit()
    db.refresh(stored_email)
    return _to_response(stored_email)


async def _parse_request(request: Request) -> ParsedEmail:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type == "application/json":
        raw_body = await _read_request_stream(request)
        try:
            manual_email = ManualEmailInput.model_validate_json(raw_body)
            return parse_manual_email(manual_email)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors(),
            ) from None

    if content_type == "multipart/form-data":
        return await _parse_multipart_request(request)

    if content_type == "message/rfc822":
        return _parse_raw_eml(await _read_request_stream(request))

    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Use application/json, multipart/form-data with an .eml file, or message/rfc822",
    )


async def _parse_multipart_request(request: Request) -> ParsedEmail:
    try:
        async with request.form(max_files=1, max_fields=10) as form:
            uploads = [value for value in form.values() if isinstance(value, StarletteUploadFile)]
            if len(uploads) != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Provide exactly one .eml file in the upload field",
                )
            upload = uploads[0]
            filename = upload.filename or ""
            content_type = (upload.content_type or "").lower()
            if not _is_eml_filename(filename):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Only .eml files are accepted",
                )
            if content_type not in ALLOWED_EML_CONTENT_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Unsupported .eml content type",
                )
            raw_message = await _read_upload(upload)
    except HTTPException:
        raise
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The multipart upload could not be read safely",
        ) from exc
    return _parse_raw_eml(raw_message)


def _parse_raw_eml(raw_message: bytes) -> ParsedEmail:
    try:
        return parse_eml(raw_message)
    except EmailParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None


async def _read_request_stream(request: Request) -> bytes:
    return await _read_chunks(request.stream())


async def _read_upload(upload: UploadFile) -> bytes:
    async def chunks() -> AsyncIterator[bytes]:
        while True:
            chunk = await upload.read(64 * 1024)
            if not chunk:
                break
            yield chunk

    return await _read_chunks(chunks())


async def _read_chunks(chunks: AsyncIterator[bytes]) -> bytes:
    data = bytearray()
    async for chunk in chunks:
        data.extend(chunk)
        if len(data) > MAX_EMAIL_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Email input exceeds the 5 MB limit",
            )
    return bytes(data)


def _is_eml_filename(filename: str) -> bool:
    normalized_filename = PureWindowsPath(filename).name
    normalized_filename = PurePosixPath(normalized_filename).name
    return normalized_filename.lower().endswith(".eml") and len(normalized_filename) <= 255


def _to_response(email: Email) -> ParsedEmailResponse:
    recipients = [recipient.strip() for recipient in email.recipient.split(",") if recipient.strip()]
    return ParsedEmailResponse(
        id=email.id,
        user_id=email.user_id,
        sender=email.sender,
        recipients=recipients,
        subject=email.subject,
        body_text=email.body_text,
        html_body=email.html_body,
        raw_headers=email.raw_headers or [],
        urls=email.extracted_urls or [],
        attachments=email.attachment_metadata or [],
        created_at=email.created_at,
        updated_at=email.updated_at,
    )
