from sqlalchemy import select
from sqlalchemy.orm import Session
from src.core.db.model.tb_category import TbCategory
from src.core.db.repository.base import BaseRepository


class CategoryRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_category_by_name(self, category_name: str) -> TbCategory:
        category = self.session.execute(
            select(TbCategory).where(TbCategory.category_name == category_name)
        ).scalar_one_or_none()
        return category

    def create_category(self, category_name: str, user_email: str) -> TbCategory:
        new_category = TbCategory(
            category_name=category_name,
            created_by=user_email,
        )
        self.session.add(new_category)
        self.session.commit()
        return new_category

    def get_all_categories(self):
        categories = self.session.execute(select(TbCategory)).scalars().all()
        return categories

    def delete_category(self, category: TbCategory):
        try:

            self.session.delete(category)
            self.session.commit()

            return True
        except Exception:
            return False
