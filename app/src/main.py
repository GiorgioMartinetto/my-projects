# app/src/main.py
import uvicorn
from fastapi import FastAPI
from src.core.config import settings
from src.core.lifespan import create_product_manager_lifespan


def create_app() -> FastAPI:
    _app = FastAPI(title=settings.app.name, lifespan=create_product_manager_lifespan())

    return _app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        app="src.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=True,
        reload_dirs=["app/src", "app/config"],
        workers=settings.app.workers,
    )
