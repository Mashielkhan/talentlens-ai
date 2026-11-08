from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://talentlens:talentlens-local-only@localhost:5432/talentlens"
    redis_url: str = "redis://localhost:6379/0"
    app_origin: str = "http://localhost:3000"
    cookie_secure: bool = False
    environment: str = "development"
    storage_path: Path = Path("data/resumes")
    storage_backend: str = "local"
    s3_bucket: str = ""
    s3_endpoint_url: str | None = None
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_revision: str = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
    spacy_model: str = "en_core_web_sm"
    demo_mode: bool = False
    require_email_verification: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_security: str = "starttls"
    upload_scanning: str = "disabled"
    clamav_host: str = "clamav"
    clamav_port: int = 3310
    max_upload_bytes: int = 10 * 1024 * 1024
    session_hours: int = 24
    semantic_weight: float = 0.45
    skills_weight: float = 0.30
    experience_weight: float = 0.15
    education_weight: float = 0.10

    @model_validator(mode="after")
    def validate_configuration(self):
        weights = [self.semantic_weight, self.skills_weight, self.experience_weight, self.education_weight]
        if min(weights) < 0 or abs(sum(weights) - 1) > 1e-6:
            raise ValueError("Scoring weights must be nonnegative and sum to one")
        if self.environment == "production" and (
            not self.cookie_secure or not self.app_origin.startswith("https://")
        ):
            raise ValueError("Production requires HTTPS and secure cookies")
        if self.storage_backend not in {"local", "s3"}:
            raise ValueError("Unknown storage backend")
        if self.smtp_security not in {"starttls", "ssl", "none"}:
            raise ValueError("Unknown SMTP security mode")
        if self.upload_scanning not in {"disabled", "clamav"}:
            raise ValueError("Unknown upload scanning mode")
        if self.environment == "production":
            if "talentlens-local-only" in self.database_url:
                raise ValueError("Production requires replacing the development database password")
            if not self.require_email_verification or not self.smtp_host or not self.smtp_from:
                raise ValueError("Public production requires email verification and configured SMTP")
            if self.smtp_security == "none" or self.upload_scanning != "clamav":
                raise ValueError("Public production requires encrypted SMTP and malware scanning")
        return self


@lru_cache
def settings():
    return Settings()
