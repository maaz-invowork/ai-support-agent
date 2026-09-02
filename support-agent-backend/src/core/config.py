from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Support Agent API"
    GOOGLE_MODEL: str = "gemini-3.6-flash"
    SECRET_KEY: str
    GOOGLE_API_KEY: str
    DATABASE_URL: str
    POSTGRES_CHECKPOINT_URL: str
    
    # Redis Configuration (for Celery)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Email Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()