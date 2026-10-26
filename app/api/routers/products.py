from dataclasses import replace

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    get_current_user,
    get_pagination,
    get_product_filters,
    get_product_service,
    require_roles,
)
from app.core.exceptions import UnprocessableError
from app.models.user import UserRole
from app.schemas.product import ProductCreate, ProductFilters, ProductRead, ProductUpdate
from app.schemas.query import Page, PaginationParams, normalize_search
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"], dependencies=[Depends(get_current_user)])

WRITE = [Depends(require_roles(UserRole.admin, UserRole.manager))]
ADMIN = [Depends(require_roles(UserRole.admin))]


@router.get("", response_model=Page[ProductRead])
def list_products(
    filters: ProductFilters = Depends(get_product_filters),
    pagination: PaginationParams = Depends(get_pagination),
    service: ProductService = Depends(get_product_service),
):
    return service.list_products(filters, pagination)


@router.get("/search", response_model=Page[ProductRead])
def search_products(
    q: str = Query(..., min_length=1, max_length=200, description="Search term for name, SKU or description"),
    filters: ProductFilters = Depends(get_product_filters),
    pagination: PaginationParams = Depends(get_pagination),
    service: ProductService = Depends(get_product_service),
):
    term = normalize_search(q)
    if term is None:
        raise UnprocessableError("Search query must not be blank")
    return service.list_products(replace(filters, search=term), pagination)


@router.get("/low-stock", response_model=Page[ProductRead])
def low_stock_products(
    filters: ProductFilters = Depends(get_product_filters),
    pagination: PaginationParams = Depends(get_pagination),
    service: ProductService = Depends(get_product_service),
):
    return service.low_stock(filters, pagination)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, service: ProductService = Depends(get_product_service)):
    return service.get(product_id)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED, dependencies=WRITE)
def create_product(data: ProductCreate, service: ProductService = Depends(get_product_service)):
    return service.create(data)


@router.put("/{product_id}", response_model=ProductRead, dependencies=WRITE)
@router.patch("/{product_id}", response_model=ProductRead, dependencies=WRITE)
def update_product(
    product_id: int,
    data: ProductUpdate,
    service: ProductService = Depends(get_product_service),
):
    return service.update(product_id, data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=ADMIN)
def delete_product(product_id: int, service: ProductService = Depends(get_product_service)):
    service.delete(product_id)
