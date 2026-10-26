from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_auth_service, get_current_user
from app.models.user import User
from app.schemas.auth import RefreshRequest, TokenPair
from app.schemas.user import UserRead, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, service: AuthService = Depends(get_auth_service)):
    return service.register(data)


@router.post("/login", response_model=TokenPair)
def login(form: OAuth2PasswordRequestForm = Depends(), service: AuthService = Depends(get_auth_service)):
    return service.login(form.username, form.password)


@router.post("/refresh", response_model=TokenPair)
def refresh(data: RefreshRequest, service: AuthService = Depends(get_auth_service)):
    return service.refresh(data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshRequest, service: AuthService = Depends(get_auth_service)):
    service.logout(data.refresh_token)


@router.get("/me", response_model=UserRead)
def me(current: User = Depends(get_current_user)):
    return current
