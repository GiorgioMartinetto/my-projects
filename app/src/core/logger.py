import contextvars
import logging
import sys
from pathlib import Path
from uuid import uuid4

from loguru import logger
from src.core.config import settings
from starlette.middleware.base import BaseHTTPMiddleware

# =============================
# ContextVar per request_id
# =============================
request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


# =============================
# Intercettazione logging stdlib
# =============================
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(
            exception=record.exc_info,
            depth=6,
        ).log(level=level, message=record.getMessage())


# =============================
# Setup Logger
# =============================
def setup_logger():

    logger.remove()

    # -------------------------
    # FORMAT
    # -------------------------

    if settings.logging.json_format:
        log_format = (
            "{"
            '"timestamp": "{time:YYYY-MM-DDTHH:mm:ss.SSSZ}",'
            '"level": "{level}",'
            '"service": "' + settings.app.name + '",'
            '"environment": "' + settings.app.environment + '",'
            '"request_id": "{extra[request_id]}",'
            '"module": "{module}",'
            '"function": "{function}",'
            '"line": {line},'
            '"message": "{message}"'
            "}"
        )
    else:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level}</level> | "
            "{extra[request_id]} | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )

    # -------------------------
    # REQUEST ID INJECTION
    # -------------------------

    def inject_request_id(record):
        record["extra"]["request_id"] = request_id_ctx.get()
        return True

    # -------------------------
    # STDOUT (SEMPRE)
    # -------------------------

    logger.add(
        sys.stdout,
        level=settings.logging.level,
        format=log_format,
        colorize=settings.logging.colorize,
        backtrace=settings.logging.backtrace,
        diagnose=settings.logging.diagnose,
        enqueue=settings.logging.enqueue,
        filter=inject_request_id,
    )

    # -------------------------
    # FILE (SOLO SE ABILITATO)
    # -------------------------

    if settings.logging.file_enabled:
        Path(settings.logging.file_path).parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            settings.logging.file_path,
            level=settings.logging.level,
            rotation=settings.logging.rotation,
            retention=settings.logging.retention,
            enqueue=settings.logging.enqueue,
            backtrace=settings.logging.backtrace,
            diagnose=settings.logging.diagnose,
            filter=inject_request_id,
        )

    # -------------------------
    # INTERCEPT LOGGING STDLIB
    # -------------------------

    logging.basicConfig(
        handlers=[InterceptHandler()],
        level=0,
        force=True,
    )

    # Evita doppio logging uvicorn
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.error").handlers = []

    return logger


# ==========================================================
# FASTAPI MIDDLEWARE
# ==========================================================
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        token = request_id_ctx.set(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx.reset(token)
