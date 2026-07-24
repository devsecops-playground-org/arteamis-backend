"""Runtime configuration.

Every value comes from the environment. Nothing sensitive has a usable default,
so a missing secret fails loudly at boot instead of silently running insecurely.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "info"
    database_url: str = "postgresql+asyncpg://arteamis:arteamis@localhost:5432/arteamis"
    jwt_secret: str = ""
    openai_api_key: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def validate_for_production(self) -> list[str]:
        """Names of secrets that production requires but does not have."""
        if not self.is_production:
            return []
        return [name for name, value in (("JWT_SECRET", self.jwt_secret),) if not value]


@lru_cache
def get_settings() -> Settings:
    return Settings()
