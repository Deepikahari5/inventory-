from decimal import Decimal

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.product import ProductFilters, ProductSortField
from app.schemas.query import PaginationParams, SortOrder, normalize_search
from app.services.auth_service import AuthService
from app.services.category_service import CategoryService
from app.services.product_service import ProductService
from app.services.supplier_service import SupplierService
from app.services.user_service import UserService

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token, "access")
    try:
        user_id = int(payload["sub"])
    except ValueError:
        raise UnauthorizedError("Invalid token subject")
    user = UserRepository(db).get(user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user


def require_roles(*roles: UserRole):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ForbiddenError()
        return user

    return checker


def get_pagination(
    page: int = Query(1, ge=1, le=settings.max_page_number, description="Page number, starting at 1"),
    page_size: int = Query(
        settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description=f"Items per page (1-{settings.max_page_size})",
    ),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


def get_search(search: str | None = Query(None, max_length=200, description="Partial, case-insensitive match on name")) -> str | None:
    return normalize_search(search)


def _build_filters(**values) -> ProductFilters:
    values["search"] = normalize_search(values.get("search"))
    return ProductFilters(**values).validated()


def get_product_filters(
    category_id: int | None = Query(None, ge=1),
    supplier_id: int | None = Query(None, ge=1),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    min_quantity: int | None = Query(None, ge=0),
    max_quantity: int | None = Query(None, ge=0),
    is_active: bool | None = Query(None),
    needs_restock: bool | None = Query(None, description="true: quantity <= reorder_level"),
    search: str | None = Query(None, max_length=200, description="Matches name, SKU or description"),
    sort_by: ProductSortField | None = Query(None),
    sort_order: SortOrder = Query(SortOrder.asc),
) -> ProductFilters:
    return _build_filters(
        category_id=category_id,
        supplier_id=supplier_id,
        min_price=min_price,
        max_price=max_price,
        min_quantity=min_quantity,
        max_quantity=max_quantity,
        is_active=is_active,
        needs_restock=needs_restock,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def get_category_product_filters(
    supplier_id: int | None = Query(None, ge=1),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    min_quantity: int | None = Query(None, ge=0),
    max_quantity: int | None = Query(None, ge=0),
    is_active: bool | None = Query(None),
    needs_restock: bool | None = Query(None, description="true: quantity <= reorder_level"),
    search: str | None = Query(None, max_length=200, description="Matches name, SKU or description"),
    sort_by: ProductSortField | None = Query(None),
    sort_order: SortOrder = Query(SortOrder.asc),
) -> ProductFilters:
    return _build_filters(
        supplier_id=supplier_id,
        min_price=min_price,
        max_price=max_price,
        min_quantity=min_quantity,
        max_quantity=max_quantity,
        is_active=is_active,
        needs_restock=needs_restock,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def get_supplier_product_filters(
    category_id: int | None = Query(None, ge=1),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    min_quantity: int | None = Query(None, ge=0),
    max_quantity: int | None = Query(None, ge=0),
    is_active: bool | None = Query(None),
    needs_restock: bool | None = Query(None, description="true: quantity <= reorder_level"),
    search: str | None = Query(None, max_length=200, description="Matches name, SKU or description"),
    sort_by: ProductSortField | None = Query(None),
    sort_order: SortOrder = Query(SortOrder.asc),
) -> ProductFilters:
    return _build_filters(
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        min_quantity=min_quantity,
        max_quantity=max_quantity,
        is_active=is_active,
        needs_restock=needs_restock,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    return CategoryService(db)


def get_supplier_service(db: Session = Depends(get_db)) -> SupplierService:
    return SupplierService(db)


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)
