from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from app.api.routes import (
    router as workflow_router,
)
from app.core.config import settings
from app.core.logging import setup_logging


setup_logging()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
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
    return {
        "status": "healthy",
        "environment": (
            settings.app_env
        ),
        "llm_model": (
            settings.groq_llm_model
        ),
        "stt_model": (
            settings.groq_stt_model
        ),
        "ocr": "paddleocr",
        "mock_mode": (
            settings.mock_mode
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )