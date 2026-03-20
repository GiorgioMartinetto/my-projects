from typing import cast

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from src.exceptions.product_exceptions.category_exception import (
    CategoryAlreadyExistsException,
    CategoryNotFoundException,
)
from starlette import status


def category_already_exists_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    app_exc = cast(CategoryAlreadyExistsException, exc)
    logger.warning(
        "Category already exists | path: {} context: {}",
        request.url.path,
        app_exc.context,
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Category already exists.",
            "code": "CATEGORY_ALREADY_EXISTS",
        },
    )


def category_not_found_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    app_exc = cast(CategoryNotFoundException, exc)

    logger.warning(
        "Category not found | path: {} context: {}",
        request.url.path,
        app_exc.context,
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": "Category not found.",
            "code": "CATEGORY_NOT_FOUND",
        },
    )
