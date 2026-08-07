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

    # Idle Session Configuration
    # DEVELOPMENT MODE: Set to 15 seconds for testing (change to 300 for production)
    IDLE_THRESHOLD_SECONDS: int = 15
    IDLE_MIN_DURATION_SECONDS: int = 15
    IDLE_BATCH_SIZE: int = 50

    # Session Batch Configuration
    SESSION_BATCH_SIZE: int = 50

    # CORS — comma-separated list of allowed origins
    # DEVELOPMENT: Includes chrome-extension:// for extension development and Vite dev server
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8000,chrome-extension://*"

    # SMTP / Email Service Configuration
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@focusguard.ai"
    SMTP_FROM_NAME: str = "FocusGuard AI Onboarding"

    # Application Base URL (used for invitation email links)
    BASE_URL: str = "http://localhost:8000"

    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Google Gemini Configuration
    GEMINI_API_KEYS: str = ""  # Comma-separated list of API keys for rotation
    GEMINI_MODEL: str = "gemini-flash-latest"  # Auto-selects working Flash model on startup

    # Grok (xAI) Configuration
    GROK_API_KEY: str = ""
    GROK_MODEL: str = "grok-4.5"

    # AI Provider Configuration
    AI_PROVIDER_ORDER: str = "gemini,grok,openai,mock"  # Comma-separated failover order

    # AI Request Configuration
    AI_REQUEST_TIMEOUT: int = 30  # seconds
    AI_MAX_RETRIES: int = 1
    AI_MAX_CONTEXT_TOKENS: int = 120000  # Maximum context tokens to send

    # AI Cache Configuration
    AI_DAILY_CACHE_TTL_HOURS: int = 4  # Daily summary cache TTL in hours
    AI_WEEKLY_CACHE_TTL_HOURS: int = 24  # Weekly summary cache TTL in hours

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("AI_PROVIDER_ORDER", mode="before")
    @classmethod
    def validate_ai_provider_order(cls, v: str) -> str:
        """Validate AI provider order configuration."""
        if isinstance(v, str):
            providers = [p.strip().lower() for p in v.split(",") if p.strip()]
        else:
            providers = ["gemini", "grok", "openai", "mock"]
        
        valid_providers = ["mock", "openai", "gemini", "grok"]
        
        for provider in providers:
            if provider not in valid_providers:
                raise ValueError(
                    f"Invalid provider '{provider}' in AI_PROVIDER_ORDER. "
                    f"Must be one of: {', '.join(valid_providers)}"
                )
        
        return ",".join(providers)

    @property
    def provider_order_list(self) -> list[str]:
        """Get provider order as a list."""
        return [p.strip().lower() for p in self.AI_PROVIDER_ORDER.split(",") if p.strip()]

    @property
    def gemini_api_keys_list(self) -> list[str]:
        """Get Gemini API keys as a list."""
        if not self.GEMINI_API_KEYS:
            return []
        return [key.strip() for key in self.GEMINI_API_KEYS.split(",") if key.strip()]

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
