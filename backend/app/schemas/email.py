"""Pydantic schemas for safe email ingestion and parsed email responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RawHeader(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    value: str = Field(max_length=10_000)

    @field_validator("name", "value")
    @classmethod
    def reject_header_injection(cls, value: str) -> str:
        if "\r" in value or "\n" in value:
            raise ValueError("Header values cannot contain line breaks")
        return value


class AttachmentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str | None = Field(default=None, max_length=255)
    content_type: str = Field(max_length=255)
    size_bytes: int | None = Field(default=None, ge=0)
    content_disposition: str | None = Field(default=None, max_length=100)


class ManualEmailInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sender: EmailStr
    recipients: list[EmailStr] = Field(min_length=1, max_length=100)
    subject: str | None = Field(default=None, max_length=998)
    body_text: str = Field(default="", max_length=5_000_000)
    html_body: str | None = Field(default=None, max_length=5_000_000)
    raw_headers: list[RawHeader] = Field(default_factory=list, max_length=200)


class ParsedEmailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    sender: EmailStr
    recipients: list[EmailStr]
    subject: str | None
    body_text: str
    html_body: str | None
    raw_headers: list[RawHeader]
    urls: list[str]
    attachments: list[AttachmentMetadata]
    created_at: datetime
    updated_at: datetime

