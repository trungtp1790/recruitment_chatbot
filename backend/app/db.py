import asyncpg

from .config import settings


def _normalize_asyncpg_dsn(dsn: str) -> str:
    if dsn.startswith("postgresql+asyncpg://"):
        return dsn.replace("postgresql+asyncpg://", "postgresql://", 1)
    return dsn


async def create_pg_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(_normalize_asyncpg_dsn(settings.database_url), min_size=1, max_size=5)
