from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.query import Page, PaginationParams
from app.schemas.user import UserCreate, UserRead, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.tokens = TokenRepository(db)

    def list_users(self, search: str | None, role: UserRole | None, is_active: bool | None, params: PaginationParams):
        items, total = self.users.list(search, role, is_active, params)
        return Page.build(UserRead, items, total, params)

    def get(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    def create(self, data: UserCreate) -> User:
        if self.users.get_by_username(data.username):
            raise ConflictError("Username already registered")
        if self.users.get_by_email(data.email):
            raise ConflictError("Email already registered")
        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role,
            is_active=data.is_active,
        )
        self.users.add(user)
        self.db.commit()
        return self.users.get(user.id)

    def update(self, user_id: int, data: UserUpdate, current: User) -> User:
        user = self.get(user_id)
        changes = data.model_dump(exclude_unset=True)
        if user.id == current.id and (changes.get("is_active") is False or changes.get("role") not in (None, current.role)):
            raise BadRequestError("You cannot change your own role or deactivate yourself")
        if "email" in changes and changes["email"] is not None and changes["email"] != user.email:
            if self.users.get_by_email(changes["email"]):
                raise ConflictError("Email already registered")
            user.email = changes["email"]
        if changes.get("password"):
            user.hashed_password = hash_password(changes["password"])
            self.tokens.revoke_all_for_user(user.id)
        if changes.get("role") is not None:
            user.role = changes["role"]
        if changes.get("is_active") is not None:
            user.is_active = changes["is_active"]
            if not user.is_active:
                self.tokens.revoke_all_for_user(user.id)
        self.db.commit()
        return self.users.get(user_id)

    def delete(self, user_id: int, current: User) -> None:
        user = self.get(user_id)
        if user.id == current.id:
            raise BadRequestError("You cannot delete your own account")
        self.users.delete(user)
        self.db.commit()
