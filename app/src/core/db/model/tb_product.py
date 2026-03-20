from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import UUID, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db.model import Base


class TbProduct(Base):
    """
    Product model for storing product information.

    Attributes:
        id: Unique identifier (UUID)
        name: Name of the product
        description: Description of the product (Optional)
        price: Price of the product
        quantity: Quantity of the product
        created_by: User that created the product
        created_at: Timestamp when the product was created
    """

    __tablename__ = "products"

    id: Mapped[UUID[str]] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4()), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    created_by: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.email"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Product(id={self.id}, name={self.name}, price={self.price},"
            f"created_by={self.created_by}, created_at={self.created_at})>"
        )
