import bcrypt
from datetime import datetime, timedelta, UTC

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app import models, schemas


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


def create_user(db: Session, payload: schemas.UserCreate) -> models.User:
    user = models.User(user_id=payload.user_id, username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise UserIdAlreadyExistsError from exc
    db.refresh(user)
    return user


def get_user(db: Session, user_pk: int) -> models.User | None:
    return db.get(models.User, user_pk)


def get_user_by_user_id(db: Session, user_id: str) -> models.User | None:
    return db.scalar(select(models.User).where(models.User.user_id == user_id))


def are_friends(db: Session, user_id: int, friend_id: int) -> bool:
    return db.execute(select(models.friendships).where(
        models.friendships.c.user_id == user_id,
        models.friendships.c.friend_id == friend_id,
    )).first() is not None


def request_status(db: Session, current_id: int, target_id: int) -> str:
    if current_id == target_id:
        return "self"
    if are_friends(db, current_id, target_id):
        return "friends"
    outgoing = db.scalar(select(models.FriendRequest).where(
        models.FriendRequest.sender_id == current_id,
        models.FriendRequest.receiver_id == target_id,
    ))
    if outgoing:
        return "requested"
    incoming = db.scalar(select(models.FriendRequest).where(
        models.FriendRequest.sender_id == target_id,
        models.FriendRequest.receiver_id == current_id,
    ))
    return "incoming" if incoming else "not_following"


def create_friend_request(db: Session, sender_id: int, receiver_id: int) -> models.FriendRequest:
    if sender_id == receiver_id:
        raise ConflictError("自分自身には申請できません")
    if are_friends(db, sender_id, receiver_id):
        raise ConflictError("すでに友だちです")
    incoming = db.scalar(select(models.FriendRequest).where(
        models.FriendRequest.sender_id == receiver_id,
        models.FriendRequest.receiver_id == sender_id,
    ))
    if incoming:
        return accept_friend_request(db, incoming, sender_id)
    request = models.FriendRequest(sender_id=sender_id, receiver_id=receiver_id)
    db.add(request)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("すでにリクエスト中です") from exc
    db.refresh(request)
    return request


def list_friend_requests(db: Session, receiver_id: int) -> list[models.FriendRequest]:
    return list(db.scalars(select(models.FriendRequest).where(
        models.FriendRequest.receiver_id == receiver_id
    ).order_by(models.FriendRequest.created_at.desc())))


def get_received_request(db: Session, request_id: int, receiver_id: int) -> models.FriendRequest | None:
    return db.scalar(select(models.FriendRequest).where(
        models.FriendRequest.id == request_id,
        models.FriendRequest.receiver_id == receiver_id,
    ))


def accept_friend_request(db: Session, request: models.FriendRequest, receiver_id: int):
    if request.receiver_id != receiver_id:
        raise ConflictError("この申請を操作する権限がありません")
    now = utc_now()
    db.execute(models.friendships.insert(), [
        {"user_id": request.sender_id, "friend_id": request.receiver_id, "last_read_at": now, "accepted_at": now},
        {"user_id": request.receiver_id, "friend_id": request.sender_id, "last_read_at": now, "accepted_at": now},
    ])
    db.delete(request)
    db.commit()
    return True


def reject_friend_request(db: Session, request: models.FriendRequest) -> None:
    db.delete(request)
    db.commit()


def cancel_friend_request(db: Session, sender_id: int, receiver_id: int) -> bool:
    request = db.scalar(select(models.FriendRequest).where(
        models.FriendRequest.sender_id == sender_id,
        models.FriendRequest.receiver_id == receiver_id,
    ))
    if not request:
        return False
    db.delete(request)
    db.commit()
    return True


def remove_friend(db: Session, user_id: int, friend_id: int) -> bool:
    result = db.execute(delete(models.friendships).where(or_(
        and_(models.friendships.c.user_id == user_id, models.friendships.c.friend_id == friend_id),
        and_(models.friendships.c.user_id == friend_id, models.friendships.c.friend_id == user_id),
    )))
    db.commit()
    return bool(result.rowcount)


def list_friends(db: Session, user_id: int) -> list[models.User]:
    return list(db.scalars(select(models.User).join(
        models.friendships, models.User.id == models.friendships.c.friend_id
    ).where(models.friendships.c.user_id == user_id).order_by(models.User.username)))


def create_post(db: Session, payload: schemas.PostCreate, user_id: int) -> models.Post:
    post = models.Post(content=payload.content, user_id=user_id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def message_history(db: Session, viewer: models.User, target: models.User) -> list[models.Post]:
    if viewer.id != target.id and not are_friends(db, viewer.id, target.id):
        raise PermissionError
    cutoff = utc_now() - timedelta(days=7)
    if viewer.id != target.id:
        accepted_at = db.scalar(select(models.friendships.c.accepted_at).where(
            models.friendships.c.user_id == viewer.id,
            models.friendships.c.friend_id == target.id,
        ))
        if accepted_at is not None:
            cutoff = max(cutoff, accepted_at)
    posts = list(db.scalars(select(models.Post).where(
        models.Post.user_id == target.id,
        models.Post.created_at >= cutoff,
    ).order_by(models.Post.created_at, models.Post.id)))
    if viewer.id != target.id:
        now = utc_now()
        db.execute(update(models.friendships).where(
            models.friendships.c.user_id == viewer.id,
            models.friendships.c.friend_id == target.id,
        ).values(last_read_at=now))
        existing = set(db.scalars(select(models.MessageRead.post_id).where(
            models.MessageRead.user_id == viewer.id,
            models.MessageRead.post_id.in_([p.id for p in posts] or [-1]),
        )))
        db.add_all(models.MessageRead(post_id=p.id, user_id=viewer.id, read_at=now) for p in posts if p.id not in existing)
        db.commit()
    return posts


def inbox(db: Session, user: models.User) -> list[dict]:
    week_ago = utc_now() - timedelta(days=7)
    friends = list_friends(db, user.id)
    result = [{"user_id": user.user_id, "username": "自分の送信履歴", "read_status": True,
               "latest_message": None, "latest_message_at": None,
               "_self": True, "_date": datetime.max}]
    own_latest = db.scalar(select(models.Post).where(
                   models.Post.user_id == user.id, models.Post.created_at >= week_ago
               ).order_by(models.Post.created_at.desc(), models.Post.id.desc()).limit(1))
    if own_latest is not None:
        result[0]["latest_message"] = own_latest.content
        result[0]["latest_message_at"] = own_latest.created_at
    for friend in friends:
        friendship = db.execute(select(
            models.friendships.c.last_read_at, models.friendships.c.accepted_at
        ).where(
            models.friendships.c.user_id == user.id,
            models.friendships.c.friend_id == friend.id,
        )).one()
        last_read, accepted_at = friendship
        cutoff = max(week_ago, accepted_at) if accepted_at is not None else week_ago
        latest = db.scalar(select(models.Post).where(
            models.Post.user_id == friend.id, models.Post.created_at >= cutoff
        ).order_by(models.Post.created_at.desc(), models.Post.id.desc()).limit(1))
        read = latest is None or (last_read is not None and latest.created_at <= last_read)
        result.append({"user_id": friend.user_id, "username": friend.username, "read_status": read,
                       "latest_message": latest.content if latest else None,
                       "latest_message_at": latest.created_at if latest else None, "_self": False,
                       "_date": latest.created_at if latest else datetime.min})
    rest = result[1:]
    rest.sort(key=lambda x: x["_date"], reverse=True)
    rest.sort(key=lambda x: x["read_status"])
    result = [result[0], *rest]
    for row in result:
        row.pop("_self", None); row.pop("_date", None)
    return result


def message_viewers(db: Session, post_id: int, owner_id: int) -> list[dict] | None:
    post = db.get(models.Post, post_id)
    if not post or post.user_id != owner_id:
        return None
    rows = db.execute(select(models.User, models.MessageRead.read_at).join(
        models.MessageRead, models.MessageRead.user_id == models.User.id
    ).where(models.MessageRead.post_id == post_id).order_by(models.MessageRead.read_at)).all()
    return [{"user_id": user.user_id, "username": user.username, "read_at": read_at} for user, read_at in rows]


def get_templates(db: Session, user_id: int):
    return list(db.scalars(
        select(models.MessageTemplate)
        .outerjoin(models.TemplateOrder, models.TemplateOrder.template_id == models.MessageTemplate.id)
        .where(models.MessageTemplate.user_id == user_id)
        .order_by(models.TemplateOrder.position.asc().nulls_last(), models.MessageTemplate.id)
    ))


def create_template(db: Session, payload: schemas.TemplateCreate, user_id: int):
    template = models.MessageTemplate(user_id=user_id, content=payload.content)
    db.add(template)
    try:
        db.flush()
        max_position = db.scalar(select(func.max(models.TemplateOrder.position)).where(models.TemplateOrder.user_id == user_id))
        db.add(models.TemplateOrder(template_id=template.id, user_id=user_id, position=(max_position or 0) + 1))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("同じ定型文が登録されています")
    db.refresh(template)
    return template


def delete_template(db: Session, template_id: int, user_id: int) -> bool:
    template = db.scalar(select(models.MessageTemplate).where(
        models.MessageTemplate.id == template_id,
        models.MessageTemplate.user_id == user_id,
    ))
    if template is None:
        return False
    db.delete(template)
    db.commit()
    return True


def reorder_templates(db: Session, template_ids: list[int], user_id: int) -> bool:
    owned_ids = list(db.scalars(select(models.MessageTemplate.id).where(
        models.MessageTemplate.user_id == user_id
    )))
    if len(template_ids) != len(set(template_ids)) or set(template_ids) != set(owned_ids):
        return False
    for position, template_id in enumerate(template_ids, start=1):
        order = db.get(models.TemplateOrder, template_id)
        if order is None:
            db.add(models.TemplateOrder(template_id=template_id, user_id=user_id, position=position))
        else:
            order.position = position
    db.commit()
    return True
