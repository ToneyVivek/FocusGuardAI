import os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FocusGuard AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database Configuration
    DATABASE_URL: str = ""

    # Security & Tokens
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # SMTP / Email Service Configuration
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@focusguard.ai"
    SMTP_FROM_NAME: str = "FocusGuard AI Onboarding"

    # Application Base URL (used for invitation email links)
    BASE_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        if isinstance(value, str):
            return value.lower().strip()
        return "development"

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        environment = info.data.get("ENVIRONMENT", "development")
        
        # Development mode: allow weak secret but require it to be set
        if environment == "development":
            if not v or v.strip() == "":
                raise ValueError(
                    "JWT_SECRET must be set in development mode. "
                    "Set a secure secret in your .env file."
                )
            if len(v) < 16:
                raise ValueError(
                    "JWT_SECRET must be at least 16 characters long even in development."
                )
            return v
        
        # Production/staging: require strong secret
        if not v or v.strip() == "":
            raise ValueError(
                "JWT_SECRET is required in production. "
                "Set a strong, random secret in your environment variables."
            )
        
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters long in production for security."
            )
        
        # Check for common weak patterns
        weak_patterns = ["secret", "password", "123456", "admin", "focusguard"]
        v_lower = v.lower()
        for pattern in weak_patterns:
            if pattern in v_lower:
                raise ValueError(
                    f"JWT_SECRET contains weak pattern '{pattern}'. "
                    "Use a cryptographically secure random secret."
                )
        
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str) -> str:
        if isinstance(value, list):
            return ",".join(value)
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
