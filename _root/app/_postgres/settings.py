from pydantic_settings import BaseSettings


class PostgresSettings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://app:app@postgres:5432/appdb"
    RETENTION_DAYS: int = 15
