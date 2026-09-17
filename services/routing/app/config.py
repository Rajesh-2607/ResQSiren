from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 4102
    osrm_base_url: str | None = None  # optional public OSRM server; falls back to straight-line

    class Config:
        env_prefix = "ROUTING_"


settings = Settings()
