from typing import Annotated, Any

from fastapi import APIRouter, Depends
from loguru import logger
from src.routers.deps import get_current_user
from src.schemas.category_request import CategoryRequest
from src.schemas.category_response import CategoryResponse, CategoryDeleteResponse
from src.services.products.category_service import (
    create_new_category,
    get_all_categories,
    delete_category,
)
from starlette import status

category_router = APIRouter(
    prefix="/category",
    tags=["Category"],
)


@category_router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    description="Create a new category",
)
def create_category(
    category: CategoryRequest,
    current_user: Annotated[dict[Any, Any], Depends(get_current_user)],
) -> CategoryResponse:
    category_name = category.name
    user_email = current_user.get("email", "")
    category_created = create_new_category(
        category_name=category_name, user_email=user_email
    )
    logger.success(
        f"Category '{category_name}' created successfully by user '{user_email}'"
    )
    return CategoryResponse.model_validate(category_created)


@category_router.get(
    "/list",
    status_code=status.HTTP_200_OK,
    summary="List all categories",
    description="List all categories",
)
def list_categories() -> list[CategoryResponse]:
    categories = get_all_categories()
    logger.success(f"Categories: {categories}")
    return [CategoryResponse.model_validate(category) for category in categories]


@category_router.delete(
    "/delete",
    status_code=status.HTTP_200_OK,
    summary="Delete a category",
    description="Delete a category",
)
def category_delete(
        category: CategoryRequest,
        current_user: Annotated[dict[Any, Any], Depends(get_current_user)],
) -> CategoryDeleteResponse:
    category_name = category.name
    check_category_delete= delete_category(category_name=category_name)
    return CategoryDeleteResponse.model_validate(check_category_delete)
