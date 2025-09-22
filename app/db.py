import asyncpg
from .config import settings

_pool: asyncpg.pool.Pool | None = None

async def get_pool() -> asyncpg.pool.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=10)
    return _pool

async def close_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
