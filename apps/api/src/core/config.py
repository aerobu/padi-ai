"""
Configuration settings for PADI.AI API.
Based on .env.example with 57+ environment variables.
"""

from functools import lru_cache
from typing import Annotated, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    PADI.AI API settings loaded from environment variables.
    Loads from .env, .env.local, or os.environ in that order.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============== App Settings ==============
    APP_NAME: str = "PADI.AI API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # ============== Database ==============
    DATABASE_URL: str
    DATABASE_POOL_MIN: int = Field(default=2, ge=0)
    DATABASE_POOL_MAX: int = Field(default=10, ge=1)

    # ============== Redis ==============
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_MIN: int = Field(default=2, ge=0)
    REDIS_POOL_MAX: int = Field(default=10, ge=1)

    # ============== Auth0 ==============
    AUTH0_SECRET: str
    AUTH0_BASE_URL: str
    AUTH0_ISSUER_BASE_URL: str
    AUTH0_CLIENT_ID: str
    AUTH0_CLIENT_SECRET: str
    AUTH0_AUDIENCE: Optional[str] = None

    # ============== LLM Routing (COPPA-compliant) ==============
    # Always uses local Ollama for student-facing features
    LLM_ROUTING__TUTOR: str = "ollama/qwen2.5:72b"
    LLM_ROUTING__ASSESSMENT: str = "ollama/qwen2.5:32b"

    # Cloud LLMs for admin/question generation only (never student-facing)
    LLM_ROUTING__QUESTION_GEN: str = "anthropic/claude-3-5-sonnet-20241022"
    LLM_ROUTING__ADMIN: str = "anthropic/claude-3-5-sonnet-20241022"

    # ============== Cloud LLM APIs ==============
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # ============== AWS ==============
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None

    # ============== AWS SES ==============
    AWS_SES_REGION: str = "us-east-1"
    AWS_SES_FROM_EMAIL: Optional[str] = None

    # ============== Stripe (MMP stage) ==============
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # ============== PostHog (COPPA-compliant analytics) ==============
    POSTHOG_API_KEY: Optional[str] = None
    POSTHOG_HOST: Optional[str] = None
    POSTHOG_PERSONAL_API_KEY: Optional[str] = None

    # ============== Sentry (error tracking) ==============
    NEXT_PUBLIC_SENTRY_DSN: Optional[str] = None
    SENTRY_AUTH_TOKEN: Optional[str] = None
    SENTRY_DSN: Optional[str] = None

    # ============== Feature Flags (Unleash) ==============
    UNLEASH_API_URL: Optional[str] = None
    UNLEASH_API_TOKEN: Optional[str] = None
    UNLEASH_APP_NAME: str = "padi-api"

    # ============== Frontend ==============
    NEXT_PUBLIC_API_BASE_URL: str = "http://localhost:8000"
    NEXT_PUBLIC_APP_VERSION: str = "0.1.0"
    NEXT_PUBLIC_SENTRY_ENVIRONMENT: str = "development"

    # ============== API Configuration ==============
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: Annotated[
        list[str], Field(default_factory=lambda: ["http://localhost:3000"])
    ]

    # ============== Rate Limiting ==============
    RATE_LIMIT_REQUESTS: int = Field(default=100, ge=1)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, ge=1)

    # ============== Session Configuration ==============
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_SAME_SITE: str = "lax"
    SESSION_MAX_AGE: int = 86400  # 24 hours

    # ============== Model Configuration ==============
    # Local Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "qwen2.5:72b"
    OLLAMA_TUTOR_MODEL: str = "qwen2.5:72b"
    OLLAMA_ASSESSMENT_MODEL: str = "qwen2.5:32b"

    # Knowledge tracing configuration
    BKT_GUESS_PROB: float = Field(default=0.1, ge=0, le=1)
    BKT_SLIP_PROB: float = Field(default=0.1, ge=0, le=1)
    BKT_LEARNING_RATE: float = Field(default=0.1, ge=0, le=1)

    # ============== Logging ==============
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ============== Timeouts ==============
    LLM_TIMEOUT_SECONDS: int = Field(default=60, ge=1)
    DB_TIMEOUT_SECONDS: int = Field(default=30, ge=1)
    CACHE_TTL_SECONDS: int = Field(default=300, ge=1)

    # ============== Compliance ==============
    COPPA_DATA_RETENTION_DAYS: int = Field(default=365, ge=1)
    STUDENT_DATA_ENCRYPTED: bool = True
    ENABLE_ANALYTICS: bool = False  # Disabled by default for COPPA compliance

    # ============== File Upload ==============
    MAX_FILE_SIZE_MB: int = Field(default=10, ge=1)
    ALLOWED_FILE_TYPES: Annotated[
        list[str],
        Field(default_factory=lambda: ["application/pdf", "image/png", "image/jpeg"]),
    ]

    # ============== Assessment Configuration ==============
    DEFAULT_ASSESSMENT_DURATION_MINUTES: int = 60
    MAX_ATTEMPTS_PER_ASSESSMENT: int = 3
    MASTERY_THRESHOLD: float = Field(default=0.85, ge=0, le=1)


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to prevent re-reading environment variables on each call.
    """
    return Settings()
