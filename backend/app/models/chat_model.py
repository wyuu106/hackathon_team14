from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from .user_model import User


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Chat(Base):
    # 既存DBのデータを維持するため、物理テーブル名は変更しない。
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String(1000))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)

    author: Mapped["User"] = relationship("User", back_populates="chats")
    reads: Mapped[list["MessageRead"]] = relationship(
        "MessageRead", back_populates="chat", cascade="all, delete-orphan"
    )


class MessageRead(Base):
    __tablename__ = "message_reads"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_message_read"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # 既存DBとの互換性を保ちつつ、Python上ではchat_idとして扱う。
    chat_id: Mapped[int] = mapped_column("post_id", ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    read_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="reads")
    user: Mapped["User"] = relationship("User")


class MessageTemplate(Base):
    __tablename__ = "message_templates"
    __table_args__ = (UniqueConstraint("user_id", "content", name="uq_template_user_content"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    owner: Mapped["User"] = relationship("User", back_populates="templates")
    order: Mapped["TemplateOrder | None"] = relationship(
        "TemplateOrder", back_populates="template", cascade="all, delete-orphan", uselist=False
    )


class TemplateOrder(Base):
    __tablename__ = "template_orders"

    template_id: Mapped[int] = mapped_column(
        ForeignKey("message_templates.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)

    template: Mapped["MessageTemplate"] = relationship("MessageTemplate", back_populates="order")
