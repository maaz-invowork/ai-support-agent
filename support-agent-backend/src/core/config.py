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

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()