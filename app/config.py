from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    redis_url: str = "redis://redis:6379/0"
    open_meteo_base_url: str = "https://api.open-meteo.com"
    open_meteo_geo_url: str = "https://geocoding-api.open-meteo.com"
    cache_ttl_seconds: int = 600
    log_level: str = "info"
    port: int = 5000


settings = Settings()
