"""Application configuration management."""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/mydb"
    LOG_DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5433/logsdb"
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SESSION_COOKIE_NAME: str = "secops_session"
    SESSION_MAX_AGE_SECONDS: int = 28800

    # Microsoft Entra ID
    ENTRA_TENANT_ID: str = ""
    ENTRA_CLIENT_ID: str = ""
    ENTRA_CLIENT_SECRET: str = ""
    ENTRA_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    ENTRA_INTERNAL_TENANT_NAME: str = "profile-service-test"
    ENTRA_IDP_NAME: str = "microsoft"
    FRONTEND_URL: str = "http://localhost:5173"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # AI oversight worker
    AI_OVERSIGHT_ENABLED: bool = True
    AI_OVERSIGHT_INTERVAL_SECONDS: int = 5
    AI_OVERSIGHT_QUEUE: str = "MS - SecOps"
    AI_OVERSIGHT_REFRESH_LIMIT: int = 500
    AI_OVERSIGHT_INCLUDE_CLOSED: bool = False

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return value
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
