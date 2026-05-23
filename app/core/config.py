from pydantic_settings import BaseSettings
from pydantic import Field, model_validator
from typing import Optional
import os

class Settings(BaseSettings):
    # Application config
    APP_NAME: str = "Sales AI Platform"
    ENV: str = Field("development", validation_alias="FLASK_ENV")
    DEBUG: bool = Field(False, validation_alias="FLASK_DEBUG")
    SECRET_KEY: str = Field("fallback-dev-secret-key-12345", validation_alias="SECRET_KEY")
    FRONTEND_URL: str = Field("http://localhost:5173", validation_alias="FRONTEND_URL")

    # Security (AES Master Key)
    ENCRYPTION_KEY: str = Field(..., validation_alias="ENCRYPTION_KEY", description="32-byte base64 encoded AES key")

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = Field(None, validation_alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(None, validation_alias="GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = Field("http://localhost:5000/api/gmail/callback", validation_alias="GOOGLE_REDIRECT_URI")

    # Database
    SUPABASE_URL: Optional[str] = Field(None, validation_alias="SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = Field(None, validation_alias="SUPABASE_SERVICE_ROLE_KEY")

    # Redis configuration
    REDIS_URL: str = Field("redis://localhost:6379/0", validation_alias="REDIS_URL")

    # Session settings
    SESSION_COOKIE_SECURE: bool = Field(True, validation_alias="SESSION_COOKIE_SECURE")
    SESSION_COOKIE_HTTPONLY: bool = Field(True, validation_alias="SESSION_COOKIE_HTTPONLY")
    SESSION_COOKIE_SAMESITE: str = Field("None", validation_alias="SESSION_COOKIE_SAMESITE")

    @property
    def cors_origins(self) -> list[str]:
        if not self.FRONTEND_URL:
            return ["http://localhost:5173"]
        return [origin.strip() for origin in self.FRONTEND_URL.split(",") if origin.strip()]

    @model_validator(mode='after')
    def validate_production_secrets(self) -> 'Settings':
        if self.ENV == 'production':
            if self.SECRET_KEY == "fallback-dev-secret-key-12345":
                raise ValueError("SECRET_KEY must be changed from the fallback in production.")
            if not self.SUPABASE_URL:
                raise ValueError("SUPABASE_URL must be configured in production.")
            if not self.SUPABASE_KEY:
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY (SUPABASE_KEY) must be configured in production.")
            if not self.ENCRYPTION_KEY or self.ENCRYPTION_KEY == "WkXQn9u0Tz_F6Jb8KxY1r5sLp3o7m4I_2BcHf_T9uD4=":
                raise ValueError("ENCRYPTION_KEY must be set to a secure, custom key in production.")
            if not self.FRONTEND_URL or "*" in self.FRONTEND_URL:
                raise ValueError("FRONTEND_URL must be set to a specific origin (not wildcard '*') in production.")
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

# Instantiate globally to be imported by other modules
settings = Settings()
