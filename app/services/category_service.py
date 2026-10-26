from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.query import Page, PaginationParams


class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.categories = CategoryRepository(db)
        self.products = ProductRepository(db)

    def list_categories(self, search: str | None, is_active: bool | None, params: PaginationParams):
        items, total = self.categories.list(search, is_active, params)
        return Page.build(CategoryRead, items, total, params)

    def get(self, category_id: int) -> Category:
        category = self.categories.get(category_id)
        if not category:
            raise NotFoundError("Category not found")
        return category

    def create(self, data: CategoryCreate) -> Category:
        if self.categories.get_by_name(data.name):
            raise ConflictError("Category name already exists")
        category = Category(**data.model_dump())
        self.categories.add(category)
        self.db.commit()
        return self.categories.get(category.id)

    def update(self, category_id: int, data: CategoryUpdate) -> Category:
        category = self.get(category_id)
        changes = data.model_dump(exclude_unset=True)
        new_name = changes.get("name")
        if new_name is not None and new_name != category.name and self.categories.get_by_name(new_name):
            raise ConflictError("Category name already exists")
        for field, value in changes.items():
            if field in ("name", "is_active") and value is None:
                continue
            setattr(category, field, value)
        self.db.commit()
        return self.categories.get(category_id)

    def delete(self, category_id: int) -> None:
        category = self.get(category_id)
        if self.products.count_by_category(category_id):
            raise ConflictError("Category has products and cannot be deleted")
        self.categories.delete(category)
        self.db.commit()
