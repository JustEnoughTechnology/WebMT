from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Mexican Train Game"
    database_url: str = "sqlite+aiosqlite:///./mexican_train.db"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    secret_key: str = "dev-secret-key-change-in-production"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
