from typing import Annotated, Any

from fastapi import APIRouter, Depends
from loguru import logger
from src.routers.deps import get_current_user
from src.schemas.product_request import (
    ProductCreationRequest,
    ProductDeleteRequest,
    ProductUpdateRequest,
)
from src.schemas.product_response import (
    ListProductsResponse,
    ProductDeletionResponse,
    ProductResponse,
)
from src.services.products.product_service import (
    get_all_products,
    get_single_product,
    product_creation,
    product_delete,
    product_to_update,
)
from starlette import status

product_router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@product_router.post(
    path="/creation",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Create a new product",
)
def creation(
    product_data: ProductCreationRequest,
    current_user: Annotated[dict[Any, Any], Depends(get_current_user)],
) -> ProductResponse:
    user_email = current_user.get("email", "")
    product_created = product_creation(
        product_data=product_data,
        user_email=user_email,
    )
    logger.success("Product created successfully: {}", product_created.name)
    return ProductResponse.model_validate(product_created)


@product_router.patch(
    path="/update",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Update an existing product",
    description="Update an existing product",
)
def product_update(
    product_data: ProductUpdateRequest,
    current_user: Annotated[dict[Any, Any], Depends(get_current_user)],
) -> ProductResponse:
    product_updated = product_to_update(
        product_data=product_data, product_owner=current_user.get("email", "")
    )
    logger.success("Product updated successfully: {}", product_updated.name)
    return ProductResponse.model_validate(product_updated)


@product_router.delete(
    path="/delete",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an existing product",
    description="Delete an existing product",
)
def delete_product(
    product: ProductDeleteRequest,
    current_user: Annotated[dict[Any, Any], Depends(get_current_user)],
) -> ProductDeletionResponse:
    created_product_by = current_user.get("email", "")
    product_deleted = product_delete(product=product, product_owner=created_product_by)
    return ProductDeletionResponse.model_validate(product_deleted)


@product_router.get(
    path="/all",
    status_code=status.HTTP_200_OK,
    summary="Get all products",
    description="Get all products",
)
def product_all() -> ListProductsResponse:
    products = get_all_products()
    logger.success("Products retrieved successfully. Total products: {}", len(products))
    return ListProductsResponse(
        products=[ProductResponse.model_validate(product) for product in products]
    )


@product_router.get(
    path="/{product_name}",
    status_code=status.HTTP_200_OK,
    summary="Get a specific product",
    description="Get a specific product",
)
def product_get(product_name: str) -> ProductResponse:
    product = get_single_product(product_name=product_name)
    logger.success("Product retrieved successfully: {}", product.name)
    return ProductResponse.model_validate(product)


# @product_router.post(
#     path="/filtered_products",
#     status_code=status.HTTP_200_OK,
#     summary="Filtered products",
#     description="Filtered products",
# )
# def product_filter():
#     pass
