from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.product import Product
from app.repositories.base import contains, paginate
from app.schemas.product import ProductFilters, ProductSortField
from app.schemas.query import PaginationParams, SortOrder

SORT_COLUMNS = {
    ProductSortField.name: Product.name,
    ProductSortField.price: Product.price,
    ProductSortField.quantity: Product.quantity,
    ProductSortField.created_at: Product.created_at,
    ProductSortField.updated_at: Product.updated_at,
}

EAGER = (joinedload(Product.category), joinedload(Product.supplier))


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, product_id: int) -> Product | None:
        return self.db.scalar(select(Product).options(*EAGER).where(Product.id == product_id))

    def get_by_sku(self, sku: str) -> Product | None:
        return self.db.scalar(select(Product).where(Product.sku == sku))

    def count_by_category(self, category_id: int) -> int:
        return self.db.scalar(select(func.count()).select_from(Product).where(Product.category_id == category_id)) or 0

    def add(self, product: Product) -> Product:
        self.db.add(product)
        self.db.flush()
        return product

    def delete(self, product: Product) -> None:
        self.db.delete(product)
        self.db.flush()

    @staticmethod
    def _conditions(filters: ProductFilters) -> list:
        conditions = []
        if filters.category_id is not None:
            conditions.append(Product.category_id == filters.category_id)
        if filters.supplier_id is not None:
            conditions.append(Product.supplier_id == filters.supplier_id)
        if filters.min_price is not None:
            conditions.append(Product.price >= filters.min_price)
        if filters.max_price is not None:
            conditions.append(Product.price <= filters.max_price)
        if filters.min_quantity is not None:
            conditions.append(Product.quantity >= filters.min_quantity)
        if filters.max_quantity is not None:
            conditions.append(Product.quantity <= filters.max_quantity)
        if filters.is_active is not None:
            conditions.append(Product.is_active == filters.is_active)
        if filters.needs_restock is True:
            conditions.append(Product.quantity <= Product.reorder_level)
        elif filters.needs_restock is False:
            conditions.append(Product.quantity > Product.reorder_level)
        if filters.search:
            conditions.append(
                or_(
                    contains(Product.name, filters.search),
                    contains(Product.sku, filters.search),
                    contains(Product.description, filters.search),
                )
            )
        return conditions

    @staticmethod
    def _ordering(filters: ProductFilters) -> list:
        column = SORT_COLUMNS.get(filters.sort_by, Product.id)
        direction = column.desc() if filters.sort_order == SortOrder.desc else column.asc()
        if column is Product.id:
            return [direction]
        return [direction, Product.id.asc()]

    def list(self, filters: ProductFilters, params: PaginationParams):
        stmt = select(Product).where(*self._conditions(filters))
        return paginate(self.db, stmt, params, order_by=self._ordering(filters), options=EAGER)
