from typing import cast

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from src.exceptions.product_exceptions.product_exception import (
    ProductAlreadyExistsException,
    ProductCanBeDeleteOnlyByTheCreatorException,
    ProductCanOnlyBeModifiedByTheCreatorException,
    ProductNotFoundException,
)
from starlette import status


def product_already_exists_handlers(request: Request, exc: Exception) -> JSONResponse:
    app_exc = cast(ProductAlreadyExistsException, exc)
    logger.warning(
        "Product already exists | path: {} context: {}",
        request.url.path,
        app_exc.context,
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Product already exists.", "code": "PRODUCT_ALREADY_EXISTS"},
    )


def product_not_found_handlers(request: Request, exc: Exception) -> JSONResponse:
    app_exc = cast(ProductNotFoundException, exc)
    logger.warning(
        "Product not found | path: {} context: {}", request.url.path, app_exc.context
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Product not found.", "code": "PRODUCT_NOT_FOUND"},
    )


def product_can_be_deleted_by_creator(request: Request, exc: Exception) -> JSONResponse:
    app_exc = cast(ProductCanBeDeleteOnlyByTheCreatorException, exc)
    logger.warning(
        "Product can't be deleted | path: {} context: {}",
        request.url.path,
        app_exc.context,
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "The product can be deleted only by its creator",
            "code": "PRODUCT_CAN_BE_DELETED_ONLY_BY_CREATOR",
        },
    )


def product_can_only_be_modified_by_the_creator(
    request: Request, exc: Exception
) -> JSONResponse:
    app_exc = cast(ProductCanOnlyBeModifiedByTheCreatorException, exc)
    logger.warning(
        "Product can only be modified by its creator. path: {} context: {}",
        request.url.path,
        app_exc.context,
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "The product can only be modified by its creator",
            "code": "PRODUCT_CAN_BE_MODIFIED_BY_CREATOR",
        },
    )
