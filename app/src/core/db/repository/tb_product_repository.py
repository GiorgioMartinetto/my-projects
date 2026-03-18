from typing import Any

from sqlalchemy import select
from src.core.db.model.tb_product import TbProduct
from src.core.db.repository.base import BaseRepository


class ProductRepository(BaseRepository):
    def __init__(self, session) -> None:
        super().__init__(session)

    # ------------------------------------------------------------------
    # Basic CRUD operations
    # ------------------------------------------------------------------
    def create_product(
        self, name: str, price: float, email: str, quantity: int, description: str
    ) -> TbProduct:
        new_product = TbProduct(
            name=name,
            description=description,
            price=price,
            quantity=quantity,
            created_by=email,
        )
        self.session.add(new_product)
        self.session.commit()
        return new_product

    def get_product_by_name(self, name: str) -> TbProduct | None:
        product = self.session.execute(
            select(TbProduct).where(TbProduct.name == name)
        ).scalar_one_or_none()
        return product

    def delete_product(self, product: TbProduct) -> bool:
        try:
            self.session.delete(product)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            return False

    def get_all_products(self) -> list[TbProduct]:
        products = self.session.execute(select(TbProduct)).scalars().all()
        return list(products)

    def update_product(self, fields: dict[str, Any], product: TbProduct) -> TbProduct:
        for key, value in fields.items():
            if hasattr(product, key):
                setattr(product, key, value)
        self.session.commit()
        self.session.refresh(product)
        return product
