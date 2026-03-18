from typing import Any

from loguru import logger
from src.core.db.database import session_scope
from src.core.db.model.tb_product import TbProduct
from src.core.db.repository.tb_product_repository import ProductRepository
from src.exceptions.product_exceptions.product_exception import (
    ProductAlreadyExistsException,
    ProductCanBeDeleteOnlyByTheCreatorException,
    ProductCanOnlyBeModifiedByTheCreatorException,
    ProductNotFoundException,
)
from src.schemas.product_request import (
    ProductCreationRequest,
    ProductDeleteRequest,
    ProductUpdateRequest,
)


def _safe_get_product_by_name(name: str) -> TbProduct | None:
    with session_scope() as session:
        repo = ProductRepository(session)
        product = repo.get_product_by_name(name=name)
        return product


def _safe_product_creation(
    name: str,
    price: float,
    quantity: int,
    email: str,
    description: str | None = None,
) -> TbProduct:
    with session_scope() as session:
        repo = ProductRepository(session)
        product = repo.create_product(
            name=name,
            price=price,
            quantity=quantity,
            email=email,
            description=description,
        )

        return product


def _safe_product_update(fields: dict[str, Any], product_owner: str) -> TbProduct:
    with session_scope() as session:
        repo = ProductRepository(session)
        product = repo.get_product_by_name(name=fields.get("name"))
        if not product:
            raise ProductNotFoundException(
                message="Product not in catalog.",
                context={
                    "product_name": fields.get("name"),
                    "product_owner": product_owner,
                },
            )

        if product.created_by != product_owner:
            raise ProductCanOnlyBeModifiedByTheCreatorException(
                message="Product can't be updated by this user.",
                context={
                    "product_name": fields.get("name"),
                    "product_owner": product_owner,
                },
            )

        if "new_name" in fields:
            fields["name"] = fields.pop("new_name")

        product_updated = repo.update_product(fields=fields, product=product)

        return product_updated


def _safe_product_deletion(name: str, product_owner: str) -> bool:
    with session_scope() as session:
        repo = ProductRepository(session)
        product = repo.get_product_by_name(name=name)
        if not product:
            raise ProductNotFoundException(
                message="Product not found.",
                context={"product_name": name, "product_owner": product_owner},
            )

        if product.created_by != product_owner:
            raise ProductCanBeDeleteOnlyByTheCreatorException(
                message="Product can't be deleted by this user.",
                context={"product_name": name, "product_owner": product_owner},
            )
        product_deleted = repo.delete_product(product=product)
        return product_deleted


def _safe_get_all_products() -> list[TbProduct]:
    with session_scope() as session:
        repo = ProductRepository(session)
        products = repo.get_all_products()
        if not products:
            raise ProductNotFoundException(
                message="Product not found.",
                context={"product_name": "", "product_owner": ""},
            )
        return products


def product_creation(
    product_data: ProductCreationRequest,
    user_email: str,
) -> TbProduct:
    existing_product = _safe_get_product_by_name(product_data.name)
    if existing_product:
        raise ProductAlreadyExistsException(
            message="Product already exists.",
            context={"product_name": product_data.name},
        )
    return _safe_product_creation(
        name=product_data.name,
        price=product_data.price,
        quantity=product_data.quantity,
        email=user_email,
        description=product_data.description,
    )


def product_to_update(
    product_data: ProductUpdateRequest,
    product_owner: str,
) -> TbProduct:

    fields = {
        field: value
        for field, value in product_data.model_dump().items()
        if value is not None
    }

    product = _safe_product_update(fields=fields, product_owner=product_owner)

    return product


def product_delete(product: ProductDeleteRequest, product_owner: str) -> dict[str, str]:
    product_name = product.name

    check_product_deleted = _safe_product_deletion(
        name=product_name, product_owner=product_owner
    )

    if check_product_deleted:
        logger.success("Product deleted successfully.")
        return {
            "message": "Product deleted.",
            "name": product_name,
        }
    logger.error("Product not deleted.")
    return {
        "message": "Product can't be deleted.",
        "name": product_name,
    }


def get_all_products() -> list[TbProduct]:
    return _safe_get_all_products()


def get_single_product(product_name: str) -> TbProduct:
    product = _safe_get_product_by_name(name=product_name)
    if not product:
        raise ProductNotFoundException(
            message="Product not found.",
            context={"product_name": product_name, "product_owner": ""},
        )
    return product
