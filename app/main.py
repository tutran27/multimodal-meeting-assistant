import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as workflow_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.pool import init_db, close_db, get_pool

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời kết nối của ứng dụng (Startup & Shutdown)."""
    logger.info("🔌 [LIFESPAN] Initializing database connection pool...")
    try:
        await init_db()
        logger.info("✅ [LIFESPAN] Database connection pool established successfully.")
    except Exception as exc:
        logger.error(f"❌ [LIFESPAN] Failed to connect to database: {exc}")

    yield

    logger.info("🔌 [LIFESPAN] Closing database connection pool...")
    try:
        await close_db()
        logger.info("🛑 [LIFESPAN] Database connection pool closed safely.")
    except Exception as exc:
        logger.error(f"❌ [LIFESPAN] Error while closing database pool: {exc}")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    workflow_router,
    prefix=settings.api_prefix,
)


@app.get("/health")
async def health() -> dict:
    db_status = "disconnected"
    try:
        pool = get_pool()
        if pool and not getattr(pool, "_closed", False):
            db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "database": db_status,
        "environment": settings.app_env,
        "llm_model": settings.groq_llm_model,
        "stt_model": settings.groq_stt_model,
        "ocr": "paddleocr",
        "mock_mode": settings.mock_mode,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )