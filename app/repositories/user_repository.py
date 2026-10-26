from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.base import contains, paginate
from app.schemas.query import PaginationParams


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self.db.scalar(select(User).where(User.username == username))

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_login(self, identifier: str) -> User | None:
        return self.db.scalar(select(User).where(or_(User.username == identifier, User.email == identifier)))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()

    def list(self, search: str | None, role: UserRole | None, is_active: bool | None, params: PaginationParams):
        stmt = select(User)
        if search:
            stmt = stmt.where(or_(contains(User.username, search), contains(User.email, search)))
        if role is not None:
            stmt = stmt.where(User.role == role)
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        return paginate(self.db, stmt, params, order_by=(User.id.asc(),))
