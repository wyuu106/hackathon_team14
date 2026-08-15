from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from .chat_model import Chat, MessageTemplate


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


friendships = Table(
    "friendships",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("friend_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("last_read_at", DateTime, nullable=True),
    Column("accepted_at", DateTime, nullable=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))

    chats: Mapped[list["Chat"]] = relationship(
        "Chat", back_populates="author", cascade="all, delete-orphan"
    )
    templates: Mapped[list["MessageTemplate"]] = relationship(
        "MessageTemplate", back_populates="owner", cascade="all, delete-orphan"
    )


class FriendRequest(Base):
    __tablename__ = "friend_requests"
    __table_args__ = (UniqueConstraint("sender_id", "receiver_id", name="uq_friend_request_pair"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id])
    receiver: Mapped["User"] = relationship("User", foreign_keys=[receiver_id])
