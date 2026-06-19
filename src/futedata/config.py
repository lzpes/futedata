"""
Centralized configuration for FuteData.

Loads settings from environment variables and .env file using pydantic-settings.
All config is validated at startup — fail fast on missing or invalid values.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Resolve project root (3 levels up from this file: src/futedata/config.py)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from .env and environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- API Keys --------------------------------------------------------
    football_data_api_key: Optional[str] = Field(
        default=None,
        description="API key for football-data.org (free tier).",
    )
    api_football_key: Optional[str] = Field(
        default=None,
        description="RapidAPI key for API-Football (optional).",
    )
    kaggle_username: Optional[str] = Field(
        default=None,
        description="Kaggle username for dataset downloads.",
    )
    kaggle_key: Optional[str] = Field(
        default=None,
        description="Kaggle API key for dataset downloads.",
    )

    # ---- Data paths ------------------------------------------------------
    data_dir: Path = Field(default=PROJECT_ROOT / "data")
    raw_dir: Path = Field(default=PROJECT_ROOT / "data" / "raw")
    validated_dir: Path = Field(default=PROJECT_ROOT / "data" / "validated")
    audit_dir: Path = Field(default=PROJECT_ROOT / "data" / "audit")

    # ---- Logging ---------------------------------------------------------
    log_level: str = Field(default="INFO")

    # ---- AWS (Phase 2+) --------------------------------------------------
    aws_region: str = Field(default="us-east-1")
    aws_profile: Optional[str] = Field(default=None)

    # ---- Databricks (Phase 4+) -------------------------------------------
    databricks_host: Optional[str] = Field(default=None)
    databricks_token: Optional[str] = Field(default=None)
    
    # ---- S3 Storage ------------------------------------------------------
    use_s3: bool = Field(default=True, description="Save data to AWS S3 instead of local disk")
    s3_raw_bucket: str = Field(default="futedata-scoutmarket-raw")
    s3_validated_bucket: str = Field(default="futedata-scoutmarket-silver")
    s3_audit_bucket: str = Field(default="futedata-scoutmarket-audit")
    s3_bronze_bucket: str = Field(default="futedata-scoutmarket-bronze")
    s3_gold_bucket: str = Field(default="futedata-scoutmarket-gold")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got '{v}'")
        return upper

    def ensure_dirs(self) -> None:
        """Create data directories if they don't exist."""
        for d in [self.data_dir, self.raw_dir, self.validated_dir, self.audit_dir]:
            d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Singleton — import this across the project
# ---------------------------------------------------------------------------
settings = Settings()
