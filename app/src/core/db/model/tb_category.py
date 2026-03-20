from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import UUID, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db.model import Base


class TbCategory(Base):
    __tablename__ = "categories"
    id: Mapped[UUID[str]] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4()), nullable=False
    )
    category_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_by: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.email"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    def __repr__(self) -> str:
        return f"<TbCategory(id={self.id}, category_name={self.category_name})>"
