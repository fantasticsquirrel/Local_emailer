from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./protonmailer.db"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    ENV: str = "dev"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-me"
    SESSION_SECRET: str = "change-me-secret"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
