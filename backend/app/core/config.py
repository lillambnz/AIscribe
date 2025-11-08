"""Application configuration."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://aiscribe:password@localhost:5432/aiscribe"

    # Security
    SECRET_KEY: str = "your-secret-key-min-32-chars-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ASR Engines
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = "australiaeast"
    WHISPER_MODEL: str = "medium"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # Storage
    STORAGE_BACKEND: str = "local"  # local, s3, azure, gcs
    STORAGE_PATH: str = "/tmp/aiscribe/audio"
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "aiscribe-audio"
    S3_REGION: str = "ap-southeast-2"
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER: str = "audio"
    GCS_BUCKET_NAME: str = "aiscribe-audio"
    GCS_CREDENTIALS_PATH: str = ""

    # Compliance & Security
    AU_DATA_RESIDENCY: bool = True
    ENCRYPTION_KEY_ID: str = "default-key"
    AUDIO_RETENTION_DAYS: int = 90
    TRANSCRIPT_RETENTION_DAYS: int = 2555  # 7 years
    ENABLE_PHI_REDACTION: bool = False
    ENABLE_LOCAL_ONLY_MODE: bool = True

    # OAuth/SSO
    OAUTH_ENABLED: bool = False
    OAUTH_CLIENT_ID: str = ""
    OAUTH_CLIENT_SECRET: str = ""
    OAUTH_TENANT_ID: str = ""
    OAUTH_AUTHORITY: str = ""
    OAUTH_REDIRECT_URI: str = ""

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Logging
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: str = ""

    # Medical NER
    ENABLE_MEDICAL_NER: bool = True
    SPACY_MODEL: str = "en_core_web_sm"

    # Diarization
    ENABLE_DIARIZATION: bool = True
    PYANNOTE_AUTH_TOKEN: str = ""


settings = Settings()
