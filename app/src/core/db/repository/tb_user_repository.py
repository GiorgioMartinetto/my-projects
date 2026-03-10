from sqlalchemy.orm import Session
from src.core.db.model.tb_user import TbUser
from src.core.db.repository.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    # ------------------------------------------------------------------
    # Basic CRUD operations
    # ------------------------------------------------------------------
    async def get_user_by_email(self, email: str) -> TbUser | None:
        """Fetch a user by their email address."""
        return self.session.query(TbUser).filter(TbUser.email == email).first()

    async def create_user(
        self, email: str, username: str, hashed_password: str
    ) -> TbUser:
        """Create a new user with the provided email, username, and hashed password."""
        new_user = TbUser(
            email=email,
            username=username,
            password_hash=hashed_password,
        )
        self.session.add(new_user)
        self.session.commit()
        return new_user
