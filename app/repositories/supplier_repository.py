from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.supplier import Supplier
from app.repositories.base import contains, paginate
from app.schemas.query import PaginationParams


class SupplierRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, supplier_id: int) -> Supplier | None:
        return self.db.get(Supplier, supplier_id)

    def add(self, supplier: Supplier) -> Supplier:
        self.db.add(supplier)
        self.db.flush()
        return supplier

    def delete(self, supplier: Supplier) -> None:
        self.db.delete(supplier)
        self.db.flush()

    def list(self, search: str | None, is_active: bool | None, params: PaginationParams):
        stmt = select(Supplier)
        if search:
            stmt = stmt.where(contains(Supplier.name, search))
        if is_active is not None:
            stmt = stmt.where(Supplier.is_active == is_active)
        return paginate(self.db, stmt, params, order_by=(Supplier.name.asc(), Supplier.id.asc()))
