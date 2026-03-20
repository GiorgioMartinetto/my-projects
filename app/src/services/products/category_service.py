
from loguru import logger
from src.core.db.database import session_scope
from src.core.db.model.tb_category import TbCategory
from src.core.db.repository.tb_category_repository import CategoryRepository
from src.exceptions.product_exceptions.category_exception import (
    CategoryAlreadyExistsException,
    CategoryNotFoundException,
)


def _safe_create_new_category(category_name: str, user_email: str) -> TbCategory:
    with session_scope() as session:
        repo = CategoryRepository(session)
        new_category = repo.create_category(
            category_name=category_name, user_email=user_email
        )
        return new_category


def _get_category_by_name(category_name):
    with session_scope() as session:
        repo = CategoryRepository(session)
        category = repo.get_category_by_name(category_name)
        return category


def _safe_all_categories():
    with session_scope() as session:
        repo = CategoryRepository(session)
        categories = repo.get_all_categories()
        return categories


def _safe_delete_category(category_name: str):
    with session_scope() as session:
        repo = CategoryRepository(session)
        existing_category = repo.get_category_by_name(category_name)
        if not existing_category:
            raise CategoryNotFoundException(
                message="Category  exists.",
                context={
                    "category_name": category_name,
                },
            )
        return repo.delete_category(category=existing_category)


def create_new_category(category_name: str, user_email: str) -> TbCategory:
    existing_category = _get_category_by_name(category_name)
    if existing_category:
        raise CategoryAlreadyExistsException(
            message="Category already exists.",
            context={
                "category_name": category_name,
            },
        )
    new_category = _safe_create_new_category(category_name, user_email)
    return new_category


def get_all_categories() -> list[TbCategory]:
    categories = _safe_all_categories()
    if not categories:
        raise CategoryNotFoundException(message="No categories found.", context={})
    return categories


def delete_category(category_name: str):
    check_category_delete = _safe_delete_category(category_name=category_name)

    if check_category_delete:
        logger.success(f"Category {category_name} deleted.")
        return {
            "message": "Category deleted successfully.",
            "category_name": category_name,
        }
    logger.error(f"Category {category_name} not found.")
    return {
        "message": "Category can't be deleted.",
        "category_name": category_name,
    }
