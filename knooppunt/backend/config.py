"""Applicatieconfiguratie uit .env (pydantic-settings)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent
# Zowel `knooppunt/.env` (naast .env.example) als `backend/.env` werkt.
_ENV_FILES = (
    str(_BACKEND_DIR / ".env"),
    str(_BACKEND_DIR.parent / ".env"),
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "sqlite:///./knooppunt.db"

    # Laag 1: licht model, enkel bij het eenmalig aanmaken van een vak.
    LAYER1_API_KEY: str = "your_api_key_here"
    LAYER1_BASE_URL: str = "https://api.deepseek.com/v1"
    LAYER1_MODEL: str = "deepseek-chat"

    # Laag 3: sterker redeneermodel, uitsluitend on-demand.
    LAYER3_API_KEY: str = "your_api_key_here"
    LAYER3_BASE_URL: str = "https://api.deepseek.com/v1"
    LAYER3_MODEL: str = "deepseek-reasoner"

    # Documentvoorverwerking
    DOCS_REPEAT_THRESHOLD: float = 0.5


settings = Settings()
