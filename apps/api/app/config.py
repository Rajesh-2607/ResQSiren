from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/resq_siren"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me-dev-secret"
    hmac_secret: str = "change-me-dispatch-hmac-secret"
    mapbox_token: str = ""
    osrm_base_url: str = "https://router.project-osrm.org"
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


settings = Settings()
