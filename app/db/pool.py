"""Quản lý Connection Pool asyncpg kết nối tới PostgreSQL (Supabase).

Nhiệm vụ & Chức năng dự kiến:
1. `init_db_pool()`:
   - Đọc `database_url` từ `app.core.config.get_settings()`.
   - Khởi tạo singleton `asyncpg.Pool` (min_size=2, max_size=10, timeout=60s).
   - Được gọi trong sự kiện `lifespan` lúc FastAPI khởi động (`app/main.py`).

2. `get_db_pool()`:
   - Trả về singleton connection pool đang hoạt động.
   - Phục vụ Dependency Injection trong FastAPI routers.

3. `close_db_pool()`:
   - Đóng toàn bộ các kết nối trong pool một cách an toàn (graceful shutdown)
     khi server tắt.

"""

import asyncpg
from app.core.config import settings

pool: asyncpg.Pool | None = None

DB_URL= settings.database_url

async def init_db():
    global pool
    if pool is None or pool.is_closed():
        pool=await asyncpg.create_pool(
            DSN=DB_URL,
            min_size=2,
            max_size=5,
            statement_cache_size=0,
        )
    return pool
   
async def close_db():
    global pool
    if pool is not None:
        await pool.close()
        pool = None

async def get_pool() -> asyncpg.Pool:
    global pool
    if pool is None or pool.is_closed():
        pool = await init_db()
    return pool

