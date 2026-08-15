from datetime import UTC, datetime

import bcrypt
from sqlalchemy import and_, delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import user_model
from app.schemas import user_schema


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class UserIdAlreadyExistsError(Exception):
    pass


class ConflictError(Exception):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_user(db: Session, payload: user_schema.UserCreate) -> user_model.User:
    user = user_model.User(
        user_id=payload.user_id,
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise UserIdAlreadyExistsError from exc
    db.refresh(user)
    return user


def get_user(db: Session, user_pk: int) -> user_model.User | None:
    return db.get(user_model.User, user_pk)


def get_user_by_user_id(db: Session, user_id: str) -> user_model.User | None:
    return db.scalar(select(user_model.User).where(user_model.User.user_id == user_id))


def are_friends(db: Session, user_id: int, friend_id: int) -> bool:
    return db.execute(select(user_model.friendships).where(
        user_model.friendships.c.user_id == user_id,
        user_model.friendships.c.friend_id == friend_id,
    )).first() is not None


def request_status(db: Session, current_id: int, target_id: int) -> str:
    if current_id == target_id:
        return "self"
    if are_friends(db, current_id, target_id):
        return "friends"
    outgoing = db.scalar(select(user_model.FriendRequest).where(
        user_model.FriendRequest.sender_id == current_id,
        user_model.FriendRequest.receiver_id == target_id,
    ))
    if outgoing:
        return "requested"
    incoming = db.scalar(select(user_model.FriendRequest).where(
        user_model.FriendRequest.sender_id == target_id,
        user_model.FriendRequest.receiver_id == current_id,
    ))
    return "incoming" if incoming else "not_following"


def create_friend_request(db: Session, sender_id: int, receiver_id: int) -> user_model.FriendRequest:
    if sender_id == receiver_id:
        raise ConflictError("自分自身には申請できません")
    if are_friends(db, sender_id, receiver_id):
        raise ConflictError("すでに友だちです")
    incoming = db.scalar(select(user_model.FriendRequest).where(
        user_model.FriendRequest.sender_id == receiver_id,
        user_model.FriendRequest.receiver_id == sender_id,
    ))
    if incoming:
        accept_friend_request(db, incoming, sender_id)
        return incoming
    request = user_model.FriendRequest(sender_id=sender_id, receiver_id=receiver_id)
    db.add(request)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("すでにリクエスト中です") from exc
    db.refresh(request)
    return request


def list_friend_requests(db: Session, receiver_id: int) -> list[user_model.FriendRequest]:
    return list(db.scalars(select(user_model.FriendRequest).where(
        user_model.FriendRequest.receiver_id == receiver_id
    ).order_by(user_model.FriendRequest.created_at.desc())))


def get_received_request(db: Session, request_id: int, receiver_id: int) -> user_model.FriendRequest | None:
    return db.scalar(select(user_model.FriendRequest).where(
        user_model.FriendRequest.id == request_id,
        user_model.FriendRequest.receiver_id == receiver_id,
    ))


def accept_friend_request(db: Session, request: user_model.FriendRequest, receiver_id: int) -> bool:
    if request.receiver_id != receiver_id:
        raise ConflictError("この申請を操作する権限がありません")
    now = utc_now()
    db.execute(user_model.friendships.insert(), [
        {"user_id": request.sender_id, "friend_id": request.receiver_id, "last_read_at": now, "accepted_at": now},
        {"user_id": request.receiver_id, "friend_id": request.sender_id, "last_read_at": now, "accepted_at": now},
    ])
    db.delete(request)
    db.commit()
    return True


def reject_friend_request(db: Session, request: user_model.FriendRequest) -> None:
    db.delete(request)
    db.commit()


def cancel_friend_request(db: Session, sender_id: int, receiver_id: int) -> bool:
    request = db.scalar(select(user_model.FriendRequest).where(
        user_model.FriendRequest.sender_id == sender_id,
        user_model.FriendRequest.receiver_id == receiver_id,
    ))
    if not request:
        return False
    db.delete(request)
    db.commit()
    return True


def remove_friend(db: Session, user_id: int, friend_id: int) -> bool:
    result = db.execute(delete(user_model.friendships).where(or_(
        and_(user_model.friendships.c.user_id == user_id, user_model.friendships.c.friend_id == friend_id),
        and_(user_model.friendships.c.user_id == friend_id, user_model.friendships.c.friend_id == user_id),
    )))
    db.commit()
    return bool(result.rowcount)


def list_friends(db: Session, user_id: int) -> list[user_model.User]:
    return list(db.scalars(select(user_model.User).join(
        user_model.friendships, user_model.User.id == user_model.friendships.c.friend_id
    ).where(user_model.friendships.c.user_id == user_id).order_by(user_model.User.username)))
