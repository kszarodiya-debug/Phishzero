"""Pydantic schemas for authentication endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


class AuthCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: SecretStr

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        password = value.get_secret_value()
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(password) > 128:
            raise ValueError("Password must be no more than 128 characters long")
        if not any(character.isalpha() for character in password):
            raise ValueError("Password must contain at least one letter")
        if not any(character.isdigit() for character in password):
            raise ValueError("Password must contain at least one digit")
        return value


class RegisterRequest(AuthCredentials):
    display_name: str | None = Field(default=None, max_length=120)


class LoginRequest(AuthCredentials):
    pass


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    display_name: str | None
    created_at: datetime
    updated_at: datetime

