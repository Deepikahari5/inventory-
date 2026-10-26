from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class TokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, jti: str, user_id: int, expires_at: datetime) -> RefreshToken:
        record = RefreshToken(jti=jti, user_id=user_id, expires_at=expires_at, revoked=False)
        self.db.add(record)
        self.db.flush()
        return record

    def get_by_jti(self, jti: str) -> RefreshToken | None:
        return self.db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))

    def revoke_all_for_user(self, user_id: int) -> None:
        self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )
