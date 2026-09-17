from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 4101
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/resq_v2"
    redis_url: str = "redis://localhost:6380/0"
    routing_service_url: str = "http://localhost:4102"
    signal_command_url: str = "http://localhost:4104"
    dispatch_hmac_secret: str = "dev-secret-change-me"

    class Config:
        env_prefix = "DISPATCH_"


settings = Settings()
