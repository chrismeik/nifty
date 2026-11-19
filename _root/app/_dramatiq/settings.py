from pydantic_settings import BaseSettings


class DramatiqSettings(BaseSettings):
    REDIS_URL: str | None = "redis://redis:6379/0"
    REDIS_BROKER_URL: str | None = None
    REDIS_CACHE_URL: str | None = None
    DLQ_KEY_PREFIX: str = "app:dlq:"
    RATE_LIMIT_PREFIX: str = "app:ratelimit:"

    @property
    def redis_broker_url(self) -> str:
        return self.REDIS_BROKER_URL or self.REDIS_URL or "redis://redis:6379/0"

    @property
    def redis_cache_url(self) -> str:
        return self.REDIS_CACHE_URL or self.REDIS_URL or "redis://redis:6379/2"
