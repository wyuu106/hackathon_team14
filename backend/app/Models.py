from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Table,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base


# ログインIDの最大文字数
USER_ID_MAX_CHARS = 30


# フォロー関係を記録する中間テーブル

follows_table = Table(
    "follows",
    Base.metadata,
    Column(
        "follower_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "followed_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    # follower_idがfollowed_idのメッセージを最後に開いた時刻。
   
    Column("last_read_at", DateTime, nullable=True),
)


class User(Base):
    __tablename__ = "users"

   
    id = Column(Integer, primary_key=True, index=True)

    # ユーザーが入力するログインID（Register.jsx / Search.jsxで入力する値）
    user_id = Column(
        String(USER_ID_MAX_CHARS),
        unique=True,
        index=True,
        nullable=False,
    )

    # 画面に表示する名前（Inbox.jsxのusername。重複可）
    username = Column(String, nullable=False)

    password_hash = Column(String, nullable=False)

    posts = relationship(
        "Post",
        back_populates="author",
        cascade="all, delete-orphan",
    )
    templates = relationship(
        "MessageTemplate",
        back_populates="owner",
        cascade="all, delete-orphan",
        order_by="MessageTemplate.id",
    )


class Post(Base):
    __tablename__ = "posts"

    
    id = Column(Integer, primary_key=True, index=True)

    content = Column(String, nullable=False)

    # users.id（数値）を参照する。ログインIDではない
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="posts")


class MessageTemplate(Base):
    """ユーザーごとの送信用定型文"""

    __tablename__ = "message_templates"

    # Send.jsxのtemplate.id（Reactのkeyと送信中判定に使う）
    id = Column(Integer, primary_key=True, index=True)

    # users.id（数値）を参照する。ログインIDではない
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  
    )

    content = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="templates")

    __table_args__ = (
        # 同じ本文のボタンが並ぶのを防ぐ
        UniqueConstraint("user_id", "content", name="uq_template_user_content"),
    )
