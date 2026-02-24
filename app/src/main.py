# app/src/main.py
import uvicorn
from fastapi import FastAPI
from src.core.config import settings
from src.core.logger import LoggingMiddleware, setup_logger

logger = setup_logger()


def create_app() -> FastAPI:
    _app = FastAPI(title=settings.app.name, version=settings.app.version)
    _app.add_middleware(LoggingMiddleware)

    return _app


app = create_app()


@app.get(path="/health_check", tags=["Health Check"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint to verify that the application is running.
    """
    logger.info("Health check endpoint called")
    return {"status": "ok", "message": "Application is healthy"}


if __name__ == "__main__":
    uvicorn.run(
        app="src.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=True,
        reload_dirs=["app/src", "app/config"],
        workers=settings.app.workers,
    )
