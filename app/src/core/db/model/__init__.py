from sqlalchemy.orm import DeclarativeBase
from src.core.db.model.user import User

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


__all__ = ["Base", "User"]


