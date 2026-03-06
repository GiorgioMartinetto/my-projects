from loguru import logger

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.exceptions.user_exception import (
    EmailAlreadyExistsException,
    UserNotFoundException,
    InvalidCredentialsException,
)


def email_already_exists_handlers(request: Request, exc: EmailAlreadyExistsException) -> JSONResponse:
    logger.warning(
        "Email already exists | path: {} context: {}",
        request.url.path,
        exc.context
    )
    return JSONResponse(
        status_code=409,
        content={"detail": "Email already exists.", "code":"EMAIL_ALREADY_EXISTS"},
    )

def user_not_found_handlers(request: Request, exc: UserNotFoundException) -> JSONResponse:
    logger.warning(
        "User not found | path: {} context: {}",
        request.url.path,
        exc.context
    )
    return JSONResponse(
        status_code=404,
        content={"detail": "User already exists.", "code":"USER_NOT_FOUND"},
    )

def invalid_credentials_handlers(request: Request, exc: InvalidCredentialsException) -> JSONResponse:
    logger.warning(
        "Invalid credential | path: {} context: {}",
        request.url.path,
        exc.context
    )
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid credentials.", "code":"INVALID_CREDENTIALS"},
    )

def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        {"field": ".".join(str(l) for l in e["loc"][1:]), "message": e["msg"]}
        for e in exc.errors()
    ]
    logger.info(
        "Input validation error | path={} errors={}",
        request.url.path,
        errors,
    )
    return JSONResponse(
        status_code=422,
        content={"detail": errors, "code": "VALIDATION_ERROR"},
    )

def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception(  # ← include automaticamente lo stack trace in loguru
        "Errore imprevisto non gestito | path={} method={} context={}",
        request.url.path,
        request.method,
        exc.__context__
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error.", "code": "INTERNAL_ERROR"},
    )