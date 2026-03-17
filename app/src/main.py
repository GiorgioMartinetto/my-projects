# app/src/main.py

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.exception_handlers import (
    email_already_exists_handlers,
    invalid_credentials_handlers,
    invalid_token_handlers,
    new_password_and_old_password_not_match_handlers,
    password_and_confirm_password_not_match_handlers,
    unhandled_exception_handler,
    user_not_found_handlers,
    validation_error_handler,
)
from src.core.logger import LoggingMiddleware, setup_logger
from src.exceptions.user_exception import (
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    InvalidTokenException,
    NewPasswordAndOldPasswordNotMatchException,
    PasswordAndConfirmPasswordNotMatchException,
    UserNotFoundException,
)
from src.routers.v1.user_endpoint import user_router

logger = setup_logger()


def create_app() -> FastAPI:
    _app = FastAPI(title=settings.app.name, version=settings.app.version)
    _app.add_middleware(LoggingMiddleware)
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # ← restringi in produzione
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _app.include_router(router=user_router)

    # Domain-specific exception handlers
    _app.add_exception_handler(
        EmailAlreadyExistsException, email_already_exists_handlers
    )
    _app.add_exception_handler(UserNotFoundException, user_not_found_handlers)
    _app.add_exception_handler(
        InvalidCredentialsException, invalid_credentials_handlers
    )
    _app.add_exception_handler(
        PasswordAndConfirmPasswordNotMatchException,
        password_and_confirm_password_not_match_handlers,
    )
    _app.add_exception_handler(InvalidTokenException, invalid_token_handlers)
    _app.add_exception_handler(
        NewPasswordAndOldPasswordNotMatchException,
        new_password_and_old_password_not_match_handlers,
    )

    # Pydantic validation error handler
    _app.add_exception_handler(RequestValidationError, validation_error_handler)

    _app.add_exception_handler(Exception, unhandled_exception_handler)

    return _app


app = create_app()


@app.get(path="/health_check", tags=["Health Check"])
def health_check() -> dict[str, str]:
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
