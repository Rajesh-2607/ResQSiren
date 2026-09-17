from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 4105
    redis_url: str = "redis://localhost:6380/0"

    class Config:
        env_prefix = "NOTIFY_"


settings = Settings()
