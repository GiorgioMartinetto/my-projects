from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import UUID, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db.model import Base


class TbUser(Base):
    """
    User model for authentication and user management.

    Attributes:
        id: Unique identifier (UUID)
        email: User's email address (unique)
        password_hash: Hashed password
        created_at: Timestamp when the user was created
        is_active: Flag to indicate if the user account is active
    """

    __tablename__ = "users"

    id: Mapped[UUID[str]] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4()), nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, email={self.email}, username={self.username},"
            f" is_active={self.is_active})>"
        )
