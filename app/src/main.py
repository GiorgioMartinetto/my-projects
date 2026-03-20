# app/src/main.py

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.logger import LoggingMiddleware, setup_logger
from src.exceptions.product_exceptions.category_exception import (
    CategoryAlreadyExistsException,
)
from src.exceptions.product_exceptions.category_exception_handlers import (
    category_already_exists_exception_handler,
)
from src.exceptions.product_exceptions.product_exception import (
    ProductAlreadyExistsException,
    ProductCanBeDeleteOnlyByTheCreatorException,
    ProductCanOnlyBeModifiedByTheCreatorException,
    ProductNotFoundException,
)
from src.exceptions.product_exceptions.product_exception_handlers import (
    product_already_exists_handlers,
    product_can_be_deleted_by_creator,
    product_can_only_be_modified_by_the_creator,
    product_not_found_handlers,
)
from src.exceptions.user_exceptions.user_exception import (
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    InvalidTokenException,
    NewPasswordAndOldPasswordNotMatchException,
    PasswordAndConfirmPasswordNotMatchException,
    UserNotFoundException,
)
from src.exceptions.user_exceptions.user_exception_handlers import (
    email_already_exists_handlers,
    invalid_credentials_handlers,
    invalid_token_handlers,
    new_password_and_old_password_not_match_handlers,
    password_and_confirm_password_not_match_handlers,
    unhandled_exception_handler,
    user_not_found_handlers,
    validation_error_handler,
)
from src.routers.v1.category_endpoint import category_router
from src.routers.v1.product_endpoint import product_router
from src.routers.v1.user_endpoint import user_router

logger = setup_logger()


def create_app() -> FastAPI:
    _app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        swagger_ui_parameters={
            "operationsSorter": "method",
            "tagsSorter": "alpha",
        },
    )
    _app.add_middleware(LoggingMiddleware)
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _app.include_router(router=user_router)
    _app.include_router(router=product_router)
    _app.include_router(router=category_router)

    # User Domain-specific exception handlers
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
    # Product Domain-specific exception handlers
    _app.add_exception_handler(
        ProductAlreadyExistsException, product_already_exists_handlers
    )
    _app.add_exception_handler(
        ProductCanBeDeleteOnlyByTheCreatorException, product_can_be_deleted_by_creator
    )

    _app.add_exception_handler(ProductNotFoundException, product_not_found_handlers)
    _app.add_exception_handler(
        ProductCanOnlyBeModifiedByTheCreatorException,
        product_can_only_be_modified_by_the_creator,
    )

    _app.add_exception_handler(
        CategoryAlreadyExistsException, category_already_exists_exception_handler
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
