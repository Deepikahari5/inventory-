from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    get_current_user,
    get_pagination,
    get_supplier_product_filters,
    get_product_service,
    get_search,
    get_supplier_service,
    require_roles,
)
from app.models.user import UserRole
from app.schemas.product import ProductFilters, ProductRead
from app.schemas.query import Page, PaginationParams
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate
from app.services.product_service import ProductService
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["Suppliers"], dependencies=[Depends(get_current_user)])

WRITE = [Depends(require_roles(UserRole.admin, UserRole.manager))]
ADMIN = [Depends(require_roles(UserRole.admin))]


@router.get("", response_model=Page[SupplierRead])
def list_suppliers(
    search: str | None = Depends(get_search),
    is_active: bool | None = Query(None),
    pagination: PaginationParams = Depends(get_pagination),
    service: SupplierService = Depends(get_supplier_service),
):
    return service.list_suppliers(search, is_active, pagination)


@router.get("/{supplier_id}", response_model=SupplierRead)
def get_supplier(supplier_id: int, service: SupplierService = Depends(get_supplier_service)):
    return service.get(supplier_id)


@router.get("/{supplier_id}/products", response_model=Page[ProductRead])
def list_supplier_products(
    supplier_id: int,
    filters: ProductFilters = Depends(get_supplier_product_filters),
    pagination: PaginationParams = Depends(get_pagination),
    service: ProductService = Depends(get_product_service),
):
    return service.list_by_supplier(supplier_id, filters, pagination)


@router.post("", response_model=SupplierRead, status_code=status.HTTP_201_CREATED, dependencies=WRITE)
def create_supplier(data: SupplierCreate, service: SupplierService = Depends(get_supplier_service)):
    return service.create(data)


@router.put("/{supplier_id}", response_model=SupplierRead, dependencies=WRITE)
@router.patch("/{supplier_id}", response_model=SupplierRead, dependencies=WRITE)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    service: SupplierService = Depends(get_supplier_service),
):
    return service.update(supplier_id, data)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=ADMIN)
def delete_supplier(supplier_id: int, service: SupplierService = Depends(get_supplier_service)):
    service.delete(supplier_id)
