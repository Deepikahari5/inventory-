from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_pagination, get_search, get_user_service, require_roles
from app.models.user import User, UserRole
from app.schemas.query import Page, PaginationParams
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(require_roles(UserRole.admin))],
)


@router.get("", response_model=Page[UserRead])
def list_users(
    search: str | None = Depends(get_search),
    role: UserRole | None = Query(None),
    is_active: bool | None = Query(None),
    pagination: PaginationParams = Depends(get_pagination),
    service: UserService = Depends(get_user_service),
):
    return service.list_users(search, role, is_active, pagination)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, service: UserService = Depends(get_user_service)):
    return service.create(data)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    return service.get(user_id)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    current: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return service.update(user_id, data, current)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    service.delete(user_id, current)
