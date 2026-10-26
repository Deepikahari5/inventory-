from dataclasses import replace

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.product import (
    ProductCreate,
    ProductFilters,
    ProductRead,
    ProductSortField,
    ProductUpdate,
)
from app.schemas.query import Page, PaginationParams


class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.products = ProductRepository(db)
        self.categories = CategoryRepository(db)
        self.suppliers = SupplierRepository(db)

    def _ensure_references(self, category_id: int | None, supplier_id: int | None) -> None:
        if category_id is not None and not self.categories.get(category_id):
            raise NotFoundError("Category not found")
        if supplier_id is not None and not self.suppliers.get(supplier_id):
            raise NotFoundError("Supplier not found")

    def list_products(self, filters: ProductFilters, params: PaginationParams) -> Page:
        items, total = self.products.list(filters, params)
        return Page.build(ProductRead, items, total, params)

    def low_stock(self, filters: ProductFilters, params: PaginationParams) -> Page:
        filters = replace(
            filters,
            needs_restock=True,
            is_active=True if filters.is_active is None else filters.is_active,
            sort_by=filters.sort_by or ProductSortField.quantity,
        )
        return self.list_products(filters, params)

    def list_by_category(self, category_id: int, filters: ProductFilters, params: PaginationParams) -> Page:
        if not self.categories.get(category_id):
            raise NotFoundError("Category not found")
        return self.list_products(replace(filters, category_id=category_id), params)

    def list_by_supplier(self, supplier_id: int, filters: ProductFilters, params: PaginationParams) -> Page:
        if not self.suppliers.get(supplier_id):
            raise NotFoundError("Supplier not found")
        return self.list_products(replace(filters, supplier_id=supplier_id), params)

    def get(self, product_id: int) -> Product:
        product = self.products.get(product_id)
        if not product:
            raise NotFoundError("Product not found")
        return product

    def create(self, data: ProductCreate) -> Product:
        self._ensure_references(data.category_id, data.supplier_id)
        if self.products.get_by_sku(data.sku):
            raise ConflictError("SKU already exists")
        product = Product(**data.model_dump())
        self.products.add(product)
        self.db.commit()
        return self.products.get(product.id)

    def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = self.get(product_id)
        changes = data.model_dump(exclude_unset=True)
        self._ensure_references(changes.get("category_id"), changes.get("supplier_id"))
        new_sku = changes.get("sku")
        if new_sku is not None and new_sku != product.sku and self.products.get_by_sku(new_sku):
            raise ConflictError("SKU already exists")
        for field, value in changes.items():
            setattr(product, field, value)
        self.db.commit()
        return self.products.get(product_id)

    def delete(self, product_id: int) -> None:
        product = self.get(product_id)
        self.products.delete(product)
        self.db.commit()
