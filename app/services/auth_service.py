from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.timeutil import utcnow
from app.models.user import User, UserRole
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenPair
from app.schemas.user import UserRegister

settings = get_settings()


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.tokens = TokenRepository(db)

    def register(self, data: UserRegister) -> User:
        if self.users.get_by_username(data.username):
            raise ConflictError("Username already registered")
        if self.users.get_by_email(data.email):
            raise ConflictError("Email already registered")
        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            role=UserRole.employee,
        )
        self.users.add(user)
        self.db.commit()
        return self.users.get(user.id)

    def _issue(self, user: User) -> TokenPair:
        access = create_access_token(user.id, user.role.value)
        refresh, jti, expires_at = create_refresh_token(user.id)
        self.tokens.add(jti, user.id, expires_at)
        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def login(self, identifier: str, password: str) -> TokenPair:
        user = self.users.get_by_login(identifier)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Incorrect username or password")
        if not user.is_active:
            raise UnauthorizedError("Account is disabled")
        pair = self._issue(user)
        self.db.commit()
        return pair

    def refresh(self, refresh_token: str) -> TokenPair:
        payload = decode_token(refresh_token, "refresh")
        record = self.tokens.get_by_jti(payload.get("jti", ""))
        if record is None:
            raise UnauthorizedError("Invalid refresh token")
        if record.revoked:
            self.tokens.revoke_all_for_user(record.user_id)
            self.db.commit()
            raise UnauthorizedError("Refresh token has been revoked")
        if record.expires_at < utcnow():
            raise UnauthorizedError("Refresh token has expired")
        user = self.users.get(record.user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("Account is disabled")
        record.revoked = True
        pair = self._issue(user)
        self.db.commit()
        return pair

    def logout(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token, "refresh")
        record = self.tokens.get_by_jti(payload.get("jti", ""))
        if record is not None and not record.revoked:
            record.revoked = True
            self.db.commit()
