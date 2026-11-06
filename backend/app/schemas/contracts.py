import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class DTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class Register(DTO):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: Literal["APPLICANT", "RECRUITER"] = "APPLICANT"
    company: str = Field(default="", max_length=160)

    @model_validator(mode="after")
    def require_company(self):
        if self.role == "RECRUITER" and not self.company.strip():
            raise ValueError("Company name is required")
        return self


class Login(DTO):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(DTO):
    id: uuid.UUID
    full_name: str
    email: str
    role: str
    profile: dict


class ProfileUpdate(DTO):
    full_name: str = Field(min_length=2, max_length=120)
    headline: str = Field(default="", max_length=200)
    location: str = Field(default="", max_length=160)
    bio: str = Field(default="", max_length=2000)
    company: str = Field(default="", max_length=160)


class PasswordUpdate(DTO):
    current_password: str = Field(max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class SkillRequirement(DTO):
    name: str = Field(min_length=1, max_length=80)
    weight: float = Field(default=1, gt=0, le=5)

    @field_validator("name")
    @classmethod
    def canonicalize(cls, value):
        from app.nlp.taxonomy import canonical_name

        return canonical_name(value.strip())


class JobInput(DTO):
    title: str = Field(min_length=3, max_length=160)
    company: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=40, max_length=30000)
    location: str = Field(default="Remote", max_length=160)
    employment_type: Literal["Full-time", "Part-time", "Contract", "Internship"] = "Full-time"
    remote_policy: Literal["Remote", "Hybrid", "On-site"] = "Remote"
    status: Literal["DRAFT", "PUBLISHED", "ARCHIVED"] = "DRAFT"
    required_skills: list[SkillRequirement] = Field(default_factory=list, max_length=80)
    preferred_skills: list[SkillRequirement] = Field(default_factory=list, max_length=80)
    min_experience_months: int = Field(default=0, ge=0, le=600)
    education_requirement: str = Field(default="", max_length=255)
    requirements_confirmed: bool = False

    @model_validator(mode="after")
    def validate_skills(self):
        names = [s.name.lower() for s in self.required_skills + self.preferred_skills]
        if len(names) != len(set(names)):
            raise ValueError("Each skill may appear only once across required and preferred skills")
        if self.status == "PUBLISHED" and not self.requirements_confirmed:
            raise ValueError("Review and confirm requirements before publishing")
        return self


class JobOut(JobInput):
    id: uuid.UUID
    recruiter_id: uuid.UUID
    version: int
    created_at: datetime


class ResumeOut(DTO):
    id: uuid.UUID
    original_filename: str
    file_size: int
    status: str
    stage: str
    error_code: str | None
    parsed_data: dict
    corrections: dict
    version: int
    created_at: datetime


class Correction(DTO):
    contact: dict[str, str] = Field(default_factory=dict, max_length=10)
    skills: list[str] = Field(default_factory=list, max_length=100)
    sections: dict[str, str] = Field(default_factory=dict, max_length=6)

    @model_validator(mode="after")
    def bounded(self):
        if any(len(v) > 300 for v in self.contact.values()) or any(len(v) > 80 for v in self.skills):
            raise ValueError("Contact or skill field too long")
        if set(self.sections) - {
            "summary",
            "skills",
            "experience",
            "education",
            "projects",
            "certifications",
        }:
            raise ValueError("Unknown section")
        if any(len(v) > 20000 for v in self.sections.values()):
            raise ValueError("Section too long")
        return self


class ApplicationInput(DTO):
    resume_id: uuid.UUID
    consent: Literal[True]


class AnalysisInput(DTO):
    resume_id: uuid.UUID
    job_id: uuid.UUID


class TaskOut(DTO):
    id: uuid.UUID
    kind: str
    status: str
    progress: int
    error_code: str | None
    result: dict


class TextInput(DTO):
    text: str = Field(min_length=20, max_length=30000)
