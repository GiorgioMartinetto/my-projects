import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from loguru import logger


def create_product_manager_lifespan(
    pipeline=None,
    *,
    app_name: str = "Product Manager API",
):
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        if pipeline is None:
            raise RuntimeError("Pipeline must be provided to lifespan")

        logger.info(f"Starting {app_name} lifespan")
        worker_task = asyncio.create_task(pipeline.start())

        try:
            yield
        finally:
            logger.info(f"Stopping {app_name} lifespan")
            await pipeline.stop()

            worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await worker_task

            logger.info(f"Waiting for {app_name} lifespan to finish")

    return lifespan
