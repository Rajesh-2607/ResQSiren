from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/resq_siren"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me-dev-secret"
    hmac_secret: str = "change-me-dispatch-hmac-secret"
    mapbox_token: str = ""
    osrm_base_url: str = "https://router.project-osrm.org"
    # Comma-separated frontend origins allowed to call the API. Needed once the
    # frontend is served from a different host than the API; in development the
    # Vite proxy makes requests same-origin so this is unused.
    cors_origins: str = "http://localhost:5173"
    fcm_server_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    gemini_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("database_url")
    @classmethod
    def _require_async_driver(cls, value: str) -> str:
        """Coerce a managed-Postgres URL into one SQLAlchemy can use async.

        Hosted Postgres (Render, Heroku, Supabase, Fly) hands out
        ``postgres://`` or ``postgresql://`` URLs. ``create_async_engine``
        resolves those to a synchronous driver and raises
        ``InvalidRequestError: The asyncio extension requires an async
        driver``, so the API would not start. asyncpg also rejects the
        ``sslmode`` query parameter that several providers append, so it is
        dropped here; asyncpg negotiates TLS on its own.
        """
        if value.startswith("postgres://"):
            value = "postgresql://" + value[len("postgres://"):]
        if value.startswith("postgresql://"):
            value = "postgresql+asyncpg://" + value[len("postgresql://"):]

        if "sslmode=" in value:
            base, _, query = value.partition("?")
            kept = [part for part in query.split("&")
                    if part and not part.startswith("sslmode=")]
            value = base + ("?" + "&".join(kept) if kept else "")

        return value


settings = Settings()
