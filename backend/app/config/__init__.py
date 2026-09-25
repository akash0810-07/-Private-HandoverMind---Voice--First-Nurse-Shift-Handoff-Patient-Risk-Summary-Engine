"""
Application configuration.

All secrets and environment-specific values are read from environment
variables. Nothing sensitive is ever hard-coded here.
"""
import os
from datetime import timedelta


def _bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


class BaseConfig:
    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    ENV = os.environ.get("FLASK_ENV", "development")
    DEMO_MODE_BANNER = "Academic demonstration system — uses synthetic patient data only."

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///handovermind_dev.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- JWT ---
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.environ.get("JWT_ACCESS_MINUTES", 30)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get("JWT_REFRESH_DAYS", 7)))
    JWT_TOKEN_LOCATION = ["headers"]

    # --- CORS ---
    CORS_ORIGINS = [
        origin if "://" in origin else f"https://{origin}"
        for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    ]

    # --- File uploads ---
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", 25)) * 1024 * 1024
    ALLOWED_AUDIO_EXTENSIONS = {"wav", "mp3", "m4a", "webm", "ogg"}
    AUDIO_STORAGE_BACKEND = os.environ.get("AUDIO_STORAGE_BACKEND", "local")  # local | s3
    AUDIO_STORAGE_PATH = os.environ.get("AUDIO_STORAGE_PATH", "/tmp/handovermind_audio")

    # --- AI providers ---
    STT_PROVIDER = os.environ.get("STT_PROVIDER", "mock")  # mock | whisper_api
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "mock")  # mock | openai
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")  # never logged, never sent to frontend
    LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "whisper-1")
    PROMPT_VERSION = "handover-summary-v1"
    AI_MAX_RETRIES = int(os.environ.get("AI_MAX_RETRIES", 2))

    # --- Rate limiting ---
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    # --- Retention ---
    AUDIO_RETENTION_DAYS = int(os.environ.get("AUDIO_RETENTION_DAYS", 30))


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    STT_PROVIDER = "mock"
    LLM_PROVIDER = "mock"


class ProductionConfig(BaseConfig):
    DEBUG = False


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return CONFIG_MAP.get(env, DevelopmentConfig)
