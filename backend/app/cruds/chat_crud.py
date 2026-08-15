from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import chat_model, user_model
from app.schemas import chat_schema

from .user_crud import ConflictError, are_friends, list_friends


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def create_chat(db: Session, payload: chat_schema.ChatCreate, user_id: int) -> chat_model.Chat:
    chat = chat_model.Chat(content=payload.content, user_id=user_id)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def message_history(
    db: Session, viewer: user_model.User, target: user_model.User
) -> list[chat_model.Chat]:
    if viewer.id != target.id and not are_friends(db, viewer.id, target.id):
        raise PermissionError
    cutoff = utc_now() - timedelta(days=7)
    if viewer.id != target.id:
        accepted_at = db.scalar(select(user_model.friendships.c.accepted_at).where(
            user_model.friendships.c.user_id == viewer.id,
            user_model.friendships.c.friend_id == target.id,
        ))
        if accepted_at is not None:
            cutoff = max(cutoff, accepted_at)
    chats = list(db.scalars(select(chat_model.Chat).where(
        chat_model.Chat.user_id == target.id,
        chat_model.Chat.created_at >= cutoff,
    ).order_by(chat_model.Chat.created_at, chat_model.Chat.id)))
    if viewer.id != target.id:
        now = utc_now()
        db.execute(update(user_model.friendships).where(
            user_model.friendships.c.user_id == viewer.id,
            user_model.friendships.c.friend_id == target.id,
        ).values(last_read_at=now))
        existing = set(db.scalars(select(chat_model.MessageRead.chat_id).where(
            chat_model.MessageRead.user_id == viewer.id,
            chat_model.MessageRead.chat_id.in_([chat.id for chat in chats] or [-1]),
        )))
        db.add_all(
            chat_model.MessageRead(chat_id=chat.id, user_id=viewer.id, read_at=now)
            for chat in chats if chat.id not in existing
        )
        db.commit()
    return chats


def inbox(db: Session, user: user_model.User) -> list[dict]:
    week_ago = utc_now() - timedelta(days=7)
    friends = list_friends(db, user.id)
    result = [{"user_id": user.user_id, "username": "自分の送信履歴", "read_status": True,
               "latest_message": None, "latest_message_at": None,
               "_self": True, "_date": datetime.max}]
    own_latest = db.scalar(select(chat_model.Chat).where(
        chat_model.Chat.user_id == user.id, chat_model.Chat.created_at >= week_ago
    ).order_by(chat_model.Chat.created_at.desc(), chat_model.Chat.id.desc()).limit(1))
    if own_latest is not None:
        result[0]["latest_message"] = own_latest.content
        result[0]["latest_message_at"] = own_latest.created_at
    for friend in friends:
        friendship = db.execute(select(
            user_model.friendships.c.last_read_at, user_model.friendships.c.accepted_at
        ).where(
            user_model.friendships.c.user_id == user.id,
            user_model.friendships.c.friend_id == friend.id,
        )).one()
        last_read, accepted_at = friendship
        cutoff = max(week_ago, accepted_at) if accepted_at is not None else week_ago
        latest = db.scalar(select(chat_model.Chat).where(
            chat_model.Chat.user_id == friend.id, chat_model.Chat.created_at >= cutoff
        ).order_by(chat_model.Chat.created_at.desc(), chat_model.Chat.id.desc()).limit(1))
        read = latest is None or (last_read is not None and latest.created_at <= last_read)
        result.append({"user_id": friend.user_id, "username": friend.username, "read_status": read,
                       "latest_message": latest.content if latest else None,
                       "latest_message_at": latest.created_at if latest else None, "_self": False,
                       "_date": latest.created_at if latest else datetime.min})
    rest = result[1:]
    rest.sort(key=lambda item: item["_date"], reverse=True)
    rest.sort(key=lambda item: item["read_status"])
    result = [result[0], *rest]
    for row in result:
        row.pop("_self", None)
        row.pop("_date", None)
    return result


def message_viewers(db: Session, chat_id: int, owner_id: int) -> list[dict] | None:
    chat = db.get(chat_model.Chat, chat_id)
    if not chat or chat.user_id != owner_id:
        return None
    rows = db.execute(select(user_model.User, chat_model.MessageRead.read_at).join(
        chat_model.MessageRead, chat_model.MessageRead.user_id == user_model.User.id
    ).where(chat_model.MessageRead.chat_id == chat_id).order_by(chat_model.MessageRead.read_at)).all()
    return [{"user_id": user.user_id, "username": user.username, "read_at": read_at} for user, read_at in rows]


def get_templates(db: Session, user_id: int) -> list[chat_model.MessageTemplate]:
    return list(db.scalars(
        select(chat_model.MessageTemplate)
        .outerjoin(chat_model.TemplateOrder, chat_model.TemplateOrder.template_id == chat_model.MessageTemplate.id)
        .where(chat_model.MessageTemplate.user_id == user_id)
        .order_by(chat_model.TemplateOrder.position.asc().nulls_last(), chat_model.MessageTemplate.id)
    ))


def create_template(db: Session, payload: chat_schema.TemplateCreate, user_id: int) -> chat_model.MessageTemplate:
    template = chat_model.MessageTemplate(user_id=user_id, content=payload.content)
    db.add(template)
    try:
        db.flush()
        max_position = db.scalar(select(func.max(chat_model.TemplateOrder.position)).where(
            chat_model.TemplateOrder.user_id == user_id
        ))
        db.add(chat_model.TemplateOrder(
            template_id=template.id, user_id=user_id, position=(max_position or 0) + 1
        ))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("同じ定型文が登録されています") from exc
    db.refresh(template)
    return template


def delete_template(db: Session, template_id: int, user_id: int) -> bool:
    template = db.scalar(select(chat_model.MessageTemplate).where(
        chat_model.MessageTemplate.id == template_id,
        chat_model.MessageTemplate.user_id == user_id,
    ))
    if template is None:
        return False
    db.delete(template)
    db.commit()
    return True


def reorder_templates(db: Session, template_ids: list[int], user_id: int) -> bool:
    owned_ids = list(db.scalars(select(chat_model.MessageTemplate.id).where(
        chat_model.MessageTemplate.user_id == user_id
    )))
    if len(template_ids) != len(set(template_ids)) or set(template_ids) != set(owned_ids):
        return False
    for position, template_id in enumerate(template_ids, start=1):
        order = db.get(chat_model.TemplateOrder, template_id)
        if order is None:
            db.add(chat_model.TemplateOrder(template_id=template_id, user_id=user_id, position=position))
        else:
            order.position = position
    db.commit()
    return True
