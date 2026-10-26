from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.supplier import Supplier
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.query import Page, PaginationParams
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate


class SupplierService:
    def __init__(self, db: Session):
        self.db = db
        self.suppliers = SupplierRepository(db)

    def list_suppliers(self, search: str | None, is_active: bool | None, params: PaginationParams):
        items, total = self.suppliers.list(search, is_active, params)
        return Page.build(SupplierRead, items, total, params)

    def get(self, supplier_id: int) -> Supplier:
        supplier = self.suppliers.get(supplier_id)
        if not supplier:
            raise NotFoundError("Supplier not found")
        return supplier

    def create(self, data: SupplierCreate) -> Supplier:
        supplier = Supplier(**data.model_dump())
        self.suppliers.add(supplier)
        self.db.commit()
        return self.suppliers.get(supplier.id)

    def update(self, supplier_id: int, data: SupplierUpdate) -> Supplier:
        supplier = self.get(supplier_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            if field in ("name", "is_active") and value is None:
                continue
            setattr(supplier, field, value)
        self.db.commit()
        return self.suppliers.get(supplier_id)

    def delete(self, supplier_id: int) -> None:
        supplier = self.get(supplier_id)
        self.suppliers.delete(supplier)
        self.db.commit()
