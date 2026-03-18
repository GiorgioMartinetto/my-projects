from typing import cast

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from src.exceptions.user_exceptions.user_exception import (
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    PasswordAndConfirmPasswordNotMatchException,
    UserNotFoundException,
)
from starlette import status


def email_already_exists_handlers(request: Request, exc: Exception) -> JSONResponse:
    app_exc = cast(EmailAlreadyExistsException, exc)
    logger.warning(
        "Email already exists | path: {} context: {}", request.url.path, app_exc.context
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Email already exists.", "code": "EMAIL_ALREADY_EXISTS"},
    )


def user_not_found_handlers(request: Request, exc: Exception) -> JSONResponse:
    app_exc = cast(UserNotFoundException, exc)
    logger.warning(
        "User not found | path: {} context: {}", request.url.path, app_exc.context
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "User already exists.", "code": "USER_NOT_FOUND"},
    )


def password_and_confirm_password_not_match_handlers(
    request: Request, exc: Exception
) -> JSONResponse:
    app_exc = cast(PasswordAndConfirmPasswordNotMatchException, exc)
    logger.warning(
        "Password and confirm password do not match | path: {} context: {}",
        request.url.path,
        app_exc.context,
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Password and confirm password do not match.",
            "code": "PASSWORD_CONFIRM_PASSWORD_NOT_MATCH",
        },
    )


def invalid_token_handlers(request: Request, exc: Exception) -> JSONResponse:
    app_exc = cast(InvalidCredentialsException, exc)
    logger.warning(
        "Invalid token | path: {} context: {}", request.url.path, app_exc.context
    )
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid token.", "code": "INVALID_TOKEN"},
    )


def invalid_credentials_handlers(request: Request, exc: Exception) -> JSONResponse:
    app_exc = cast(InvalidCredentialsException, exc)
    logger.warning(
        "Invalid credential | path: {} context: {}", request.url.path, app_exc.context
    )
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid credentials.", "code": "INVALID_CREDENTIALS"},
    )


def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    app_exc = cast(RequestValidationError, exc)
    errors = [
        {"field": ".".join(str(loc) for loc in e["loc"][1:]), "message": e["msg"]}
        for e in app_exc.errors()
    ]
    logger.info(
        "Input validation error | path={} errors={}",
        request.url.path,
        errors,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": errors, "code": "VALIDATION_ERROR"},
    )


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(  # ← include automaticamente lo stack trace in loguru
        "Errore imprevisto non gestito | path={} method={} context={}",
        request.url.path,
        request.method,
        exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error.", "code": "INTERNAL_ERROR"},
    )


def new_password_and_old_password_not_match_handlers(
    request: Request, exc: Exception
) -> JSONResponse:
    app_exc = cast(PasswordAndConfirmPasswordNotMatchException, exc)

    logger.warning(
        "New password and old password do not match | path: {} context: {}",
        request.url.path,
        app_exc.context,
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "New password and old password do not match.",
            "code": "NEW_PASSWORD_OLD_PASSWORD_NOT_MATCH",
        },
    )
