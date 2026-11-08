import uuid
from datetime import datetime
from typing import Literal

from pydantic import EmailStr, Field, field_validator

from app.schemas.contracts import DTO


class CvContent(DTO):
    name: str = Field(default="", max_length=120)
    email: str = Field(default="", max_length=254)
    phone: str = Field(default="", max_length=100)
    links: str = Field(default="", max_length=1000)
    summary: str = Field(default="", max_length=4000)
    skills: str = Field(default="", max_length=4000)
    experience: str = Field(default="", max_length=15000)
    education: str = Field(default="", max_length=6000)
    projects: str = Field(default="", max_length=10000)
    certifications: str = Field(default="", max_length=4000)

    @field_validator("*")
    @classmethod
    def clean(cls, value):
        # Avoid XML-invalid controls in DOCX; preserve ordinary line breaks.
        return "".join(
            c
            for c in value
            if c in "\n\t"
            or 0x20 <= ord(c) <= 0xD7FF
            or 0xE000 <= ord(c) <= 0xFFFD
            or 0x10000 <= ord(c) <= 0x10FFFF
        ).strip()


class DraftCreate(DTO):
    resume_id: uuid.UUID
    title: str = Field(min_length=3, max_length=160)
    target_description: str = Field(min_length=40, max_length=20000)


class DraftUpdate(DTO):
    revision: int = Field(ge=1)
    content: CvContent


class DraftApprove(DTO):
    revision: int = Field(ge=1)
    facts_confirmed: Literal[True]


class DraftOut(DTO):
    id: uuid.UUID
    resume_id: uuid.UUID
    source_version: int
    title: str
    target_description: str
    original: CvContent
    content: CvContent
    guidance: dict
    revision: int
    approved_revision: int | None
    created_at: datetime
    source_outdated: bool = False


class EmailRequest(DTO):
    email: EmailStr


class TokenInput(DTO):
    token: str = Field(min_length=32, max_length=200)


class ResetInput(TokenInput):
    new_password: str = Field(min_length=12, max_length=128)


class FeedbackInput(DTO):
    category: Literal["bug", "suggestion", "other"]
    message: str = Field(min_length=10, max_length=3000)

    @field_validator("message", mode="before")
    @classmethod
    def trim_message(cls, value):
        return value.strip() if isinstance(value, str) else value
