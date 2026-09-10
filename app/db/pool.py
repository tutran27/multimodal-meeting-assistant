"""Quản lý Connection Pool asyncpg kết nối tới PostgreSQL (Supabase)."""
import logging
import asyncpg
from app.core.config import settings

logger = logging.getLogger(__name__)

pool: asyncpg.Pool | None = None


async def init_db() -> asyncpg.Pool:
    """Khởi tạo singleton connection pool tới database."""
    global pool
    if pool is None or getattr(pool, "_closed", False):
        pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
            command_timeout=settings.db_pool_timeout,
            statement_cache_size=0,
        )
    return pool


async def close_db() -> None:
    """Đóng toàn bộ các kết nối trong pool một cách an toàn."""
    global pool
    if pool is not None:
        await pool.close()
        pool = None


def get_pool() -> asyncpg.Pool:
    """Lấy connection pool hiện tại. Ném lỗi nếu chưa khởi tạo qua lifespan."""
    global pool
    if pool is None or getattr(pool, "_closed", False):
        raise RuntimeError("Database pool chưa được khởi tạo. Hãy đảm bảo lifespan đã chạy 'await init_db()'.")
    return pool
