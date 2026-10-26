from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    get_category_service,
    get_current_user,
    get_pagination,
    get_category_product_filters,
    get_product_service,
    get_search,
    require_roles,
)
from app.models.user import UserRole
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.product import ProductFilters, ProductRead
from app.schemas.query import Page, PaginationParams
from app.services.category_service import CategoryService
from app.services.product_service import ProductService

router = APIRouter(prefix="/categories", tags=["Categories"], dependencies=[Depends(get_current_user)])

WRITE = [Depends(require_roles(UserRole.admin, UserRole.manager))]
ADMIN = [Depends(require_roles(UserRole.admin))]


@router.get("", response_model=Page[CategoryRead])
def list_categories(
    search: str | None = Depends(get_search),
    is_active: bool | None = Query(None),
    pagination: PaginationParams = Depends(get_pagination),
    service: CategoryService = Depends(get_category_service),
):
    return service.list_categories(search, is_active, pagination)


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, service: CategoryService = Depends(get_category_service)):
    return service.get(category_id)


@router.get("/{category_id}/products", response_model=Page[ProductRead])
def list_category_products(
    category_id: int,
    filters: ProductFilters = Depends(get_category_product_filters),
    pagination: PaginationParams = Depends(get_pagination),
    service: ProductService = Depends(get_product_service),
):
    return service.list_by_category(category_id, filters, pagination)


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED, dependencies=WRITE)
def create_category(data: CategoryCreate, service: CategoryService = Depends(get_category_service)):
    return service.create(data)


@router.put("/{category_id}", response_model=CategoryRead, dependencies=WRITE)
@router.patch("/{category_id}", response_model=CategoryRead, dependencies=WRITE)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    service: CategoryService = Depends(get_category_service),
):
    return service.update(category_id, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=ADMIN)
def delete_category(category_id: int, service: CategoryService = Depends(get_category_service)):
    service.delete(category_id)
