from __future__ import annotations

from functools import lru_cache
from typing import Final

from _app._postgres.settings import PostgresSettings
from _app._dramatiq.settings import DramatiqSettings
from _app._fastapi.settings import FastAPISettings
from _app._postgres.bootstrap import init as postgres_init


class Settings(PostgresSettings, DramatiqSettings, FastAPISettings):
    pass


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings: Final[Settings] = get_settings()


async def bootstrap():
    await postgres_init()
    try:
        from _app._graphiti.bootstrap import init as graphiti_init
        await graphiti_init()
    except ImportError:
        pass


__all__ = ["Settings", "get_settings", "settings", "bootstrap"]
