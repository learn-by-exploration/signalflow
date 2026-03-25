"""Authentication Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    telegram_chat_id: int | None = Field(default=None, gt=0)


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class UserProfile(BaseModel):
    """User profile response."""

    id: UUID
    email: str
    telegram_chat_id: int | None = None
    tier: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
