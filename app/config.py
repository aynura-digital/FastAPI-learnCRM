from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_SECRET_PLACEHOLDER = "CHANGE-ME-IN-PRODUCTION"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "LearnCRM Sync API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./learncrm.db"

    # JWT
    secret_key: str = INSECURE_SECRET_PLACEHOLDER
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # API Key
    api_key: str = INSECURE_SECRET_PLACEHOLDER

    # Rate Limiting
    rate_limit: str = "100/minute"

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8080"

    # Logging
    log_level: str = "INFO"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @model_validator(mode="after")
    def _refuse_insecure_secrets_in_prod(self) -> "Settings":
        if self.debug:
            return self
        insecure = [
            name
            for name, value in (("secret_key", self.secret_key), ("api_key", self.api_key))
            if value == INSECURE_SECRET_PLACEHOLDER
        ]
        if insecure:
            raise ValueError(
                "Refusing to start with default placeholder secrets in non-debug mode: "
                + ", ".join(insecure)
                + ". Set them via environment variables or .env."
            )
        return self


settings = Settings()
