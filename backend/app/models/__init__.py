from datetime import datetime, UTC

from sqlalchemy import DateTime, ForeignKey, String, Table, Column, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


friendships = Table(
    "friendships",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("friend_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("last_read_at", DateTime, nullable=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))

    posts: Mapped[list["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    templates: Mapped[list["MessageTemplate"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class FriendRequest(Base):
    __tablename__ = "friend_requests"
    __table_args__ = (UniqueConstraint("sender_id", "receiver_id", name="uq_friend_request_pair"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    sender: Mapped[User] = relationship(foreign_keys=[sender_id])
    receiver: Mapped[User] = relationship(foreign_keys=[receiver_id])


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String(1000))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)

    author: Mapped[User] = relationship(back_populates="posts")
    reads: Mapped[list["MessageRead"]] = relationship(back_populates="post", cascade="all, delete-orphan")


class MessageRead(Base):
    __tablename__ = "message_reads"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_message_read"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    read_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    post: Mapped[Post] = relationship(back_populates="reads")
    user: Mapped[User] = relationship()


class MessageTemplate(Base):
    __tablename__ = "message_templates"
    __table_args__ = (UniqueConstraint("user_id", "content", name="uq_template_user_content"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    owner: Mapped[User] = relationship(back_populates="templates")
    order: Mapped["TemplateOrder | None"] = relationship(back_populates="template", cascade="all, delete-orphan", uselist=False)


class TemplateOrder(Base):
    __tablename__ = "template_orders"

    template_id: Mapped[int] = mapped_column(ForeignKey("message_templates.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)

    template: Mapped[MessageTemplate] = relationship(back_populates="order")
