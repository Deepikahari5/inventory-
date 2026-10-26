from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.base import contains, paginate
from app.schemas.query import PaginationParams


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, category_id: int) -> Category | None:
        return self.db.get(Category, category_id)

    def get_by_name(self, name: str) -> Category | None:
        return self.db.scalar(select(Category).where(Category.name == name))

    def add(self, category: Category) -> Category:
        self.db.add(category)
        self.db.flush()
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.flush()

    def list(self, search: str | None, is_active: bool | None, params: PaginationParams):
        stmt = select(Category)
        if search:
            stmt = stmt.where(contains(Category.name, search))
        if is_active is not None:
            stmt = stmt.where(Category.is_active == is_active)
        return paginate(self.db, stmt, params, order_by=(Category.name.asc(), Category.id.asc()))
