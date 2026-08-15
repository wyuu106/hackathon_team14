import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.user_model import RefreshSession


class InvalidRefreshTokenError(Exception):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_refresh_session(
    db: Session,
    user_id: int,
    lifetime_days: int,
    token_family: str | None = None,
) -> tuple[str, RefreshSession]:
    token = secrets.token_urlsafe(48)
    session = RefreshSession(
        user_id=user_id,
        token_hash=hash_refresh_token(token),
        token_family=token_family or str(uuid4()),
        expires_at=utc_now() + timedelta(days=lifetime_days),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return token, session


def rotate_refresh_session(
    db: Session,
    token: str,
    lifetime_days: int,
) -> tuple[str, RefreshSession]:
    token_hash = hash_refresh_token(token)
    current = db.scalar(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash)
    )
    if current is None:
        raise InvalidRefreshTokenError

    now = utc_now()
    if current.revoked_at is not None:
        revoke_token_family(db, current.token_family, now)
        raise InvalidRefreshTokenError
    if current.expires_at <= now:
        current.revoked_at = now
        db.commit()
        raise InvalidRefreshTokenError

    new_token = secrets.token_urlsafe(48)
    new_session = RefreshSession(
        user_id=current.user_id,
        token_hash=hash_refresh_token(new_token),
        token_family=current.token_family,
        expires_at=now + timedelta(days=lifetime_days),
    )
    current.last_used_at = now
    current.revoked_at = now
    current.replaced_by_hash = new_session.token_hash
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_token, new_session


def revoke_token_family(
    db: Session,
    token_family: str,
    revoked_at: datetime | None = None,
) -> None:
    db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.token_family == token_family,
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=revoked_at or utc_now())
    )
    db.commit()


def revoke_refresh_token(db: Session, token: str) -> None:
    session = db.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == hash_refresh_token(token)
        )
    )
    if session is not None:
        revoke_token_family(db, session.token_family)
