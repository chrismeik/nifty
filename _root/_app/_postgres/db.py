from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

try:
    from .settings import get_settings
    DATABASE_URL = get_settings().DATABASE_URL
except Exception:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://app:app@postgres:5432/appdb",
    )

# DB_NULLPOOL=1 disables connection pooling. Needed where several threads each
# run their own event loop (e.g. dramatiq worker threads calling asyncio.run),
# since pooled asyncpg connections are bound to the loop that created them.
if os.getenv("DB_NULLPOOL") == "1":
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
else:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
