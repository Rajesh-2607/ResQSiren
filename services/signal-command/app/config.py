from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 4104
    redis_url: str = "redis://localhost:6380/0"
    dispatch_hmac_secret: str = "dev-secret-change-me"

    class Config:
        env_prefix = "SIGNAL_"


settings = Settings()
