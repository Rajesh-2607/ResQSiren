from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 4103
    redis_url: str = "redis://localhost:6380/0"
    dispatch_hmac_secret: str = "dev-secret-change-me"
    signal_command_url: str = "http://localhost:4104"
    tick_interval_seconds: float = 1.0
    claim_ttl_seconds: int = 25  # a claim not refreshed within this window is dropped (ambulance cleared / lost signal)

    class Config:
        env_prefix = "CONFLICT_"


settings = Settings()
