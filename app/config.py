"""
Application configuration using Pydantic settings
Centralized configuration management with environment variable validation
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Configuration
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash-exp", alias="GEMINI_MODEL")

    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    reload: bool = Field(default=True, alias="RELOAD")

    # Audio Configuration
    audio_sample_rate: int = Field(default=16000, alias="AUDIO_SAMPLE_RATE")
    audio_chunk_size: int = Field(default=512, alias="AUDIO_CHUNK_SIZE")

    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Audio flush interval (magic number now configurable)
    # This is ~5 seconds of audio at 16kHz (16000 Hz * 2 bytes * 5s = 160000 bytes)
    flush_interval_bytes: int = Field(default=160000, alias="FLUSH_INTERVAL_BYTES")

    @field_validator("gemini_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Ensure API key is not empty"""
        if not v or v.strip() == "":
            raise ValueError("GEMINI_API_KEY cannot be empty")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Ensure port is in valid range"""
        if not 1 <= v <= 65535:
            raise ValueError("PORT must be between 1 and 65535")
        return v


# Global settings instance
settings = Settings()
