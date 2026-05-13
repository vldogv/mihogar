from pydantic_settings import BaseSettings
from functools import lru_cache
import json


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://mihogar_admin:mihogar_local_2026@localhost:5432/mihogar"
    DATABASE_URL_SYNC: str = "postgresql://mihogar_admin:mihogar_local_2026@localhost:5432/mihogar"

    JWT_SECRET: str = "local-dev-secret-change-in-prod-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 480

    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:5173"]'
    ENV: str = "development"

    @property
    def cors_origins_list(self) -> list[str]:
        return json.loads(self.CORS_ORIGINS)

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
