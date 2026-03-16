from sqlalchemy.orm import Session
from src.core.db.model.tb_user import TbUser
from src.core.db.repository.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    # ------------------------------------------------------------------
    # Basic CRUD operations
    # ------------------------------------------------------------------
    def get_user_by_email(self, email: str) -> TbUser | None:
        """Fetch a user by their email address."""
        return self.session.query(TbUser).filter(TbUser.email == email).first()

    def create_user(self, email: str, username: str, hashed_password: str) -> TbUser:
        """Create a new user with the provided email, username, and hashed password."""
        new_user = TbUser(
            email=email,
            username=username,
            password_hash=hashed_password,
        )
        self.session.add(new_user)
        self.session.commit()
        return new_user

    def update_user(self, email, fields) -> type[TbUser] | None:
        """Update an existing user's fields based on their email."""
        user = self.session.query(TbUser).filter(TbUser.email == email).first()
        if not user:
            return None
        for key, value in fields.items():
            setattr(user, key, value)
        self.session.add(user)
        self.session.commit()
        return user

    def delete_user(self, email: str) -> type[TbUser] | None:
        """Delete an existing user's fields based on their email."""
        user = self.session.query(TbUser).filter(TbUser.email == email).first()
        if not user:
            return None
        self.session.delete(user)
        self.session.commit()
        return user
