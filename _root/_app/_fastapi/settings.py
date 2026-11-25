from pydantic_settings import BaseSettings


class FastAPISettings(BaseSettings):
    REQUEST_MAX_BODY_MB: int = 50
    ALLOWED_ORIGINS: str = ""
    ASTRO_URL: str = "http://localhost"
    LOG_LEVEL: str = "INFO"
