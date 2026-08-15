"""Alembic導入時点のスキーマを作成する。

Revision ID: 20260816_0001
Revises:
Create Date: 2026-08-16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260816_0001"
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    return index_name in {
        index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)
    }


def _create_index_if_missing(
    name: str,
    table_name: str,
    columns: list[str],
    *,
    unique: bool = False,
) -> None:
    if not _index_exists(table_name, name):
        op.create_index(name, table_name, columns, unique=unique)


def upgrade() -> None:
    if not _table_exists("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.String(length=30), nullable=False),
            sa.Column("username", sa.String(length=100), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
        )
    _create_index_if_missing("ix_users_user_id", "users", ["user_id"], unique=True)

    if not _table_exists("friendships"):
        op.create_table(
            "friendships",
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("friend_id", sa.Integer(), nullable=False),
            sa.Column("last_read_at", sa.DateTime(), nullable=True),
            sa.Column("accepted_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["friend_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "friend_id"),
        )
    else:
        friendship_columns = {
            column["name"]
            for column in sa.inspect(op.get_bind()).get_columns("friendships")
        }
        if "accepted_at" not in friendship_columns:
            op.add_column("friendships", sa.Column("accepted_at", sa.DateTime(), nullable=True))

    if not _table_exists("friend_requests"):
        op.create_table(
            "friend_requests",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("sender_id", sa.Integer(), nullable=False),
            sa.Column("receiver_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["receiver_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("sender_id", "receiver_id", name="uq_friend_request_pair"),
        )
    _create_index_if_missing("ix_friend_requests_receiver_id", "friend_requests", ["receiver_id"])
    _create_index_if_missing("ix_friend_requests_sender_id", "friend_requests", ["sender_id"])

    if not _table_exists("posts"):
        op.create_table(
            "posts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("content", sa.String(length=1000), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
    _create_index_if_missing("ix_posts_created_at", "posts", ["created_at"])
    _create_index_if_missing("ix_posts_user_id", "posts", ["user_id"])

    if not _table_exists("message_templates"):
        op.create_table(
            "message_templates",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("content", sa.String(length=100), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("user_id", "content", name="uq_template_user_content"),
        )
    _create_index_if_missing("ix_message_templates_user_id", "message_templates", ["user_id"])

    if not _table_exists("refresh_sessions"):
        op.create_table(
            "refresh_sessions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("token_family", sa.String(length=36), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("last_used_at", sa.DateTime(), nullable=True),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.Column("replaced_by_hash", sa.String(length=64), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
    _create_index_if_missing("ix_refresh_sessions_expires_at", "refresh_sessions", ["expires_at"])
    _create_index_if_missing("ix_refresh_sessions_token_family", "refresh_sessions", ["token_family"])
    _create_index_if_missing("ix_refresh_sessions_token_hash", "refresh_sessions", ["token_hash"], unique=True)
    _create_index_if_missing("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"])

    if not _table_exists("message_reads"):
        op.create_table(
            "message_reads",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("post_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("read_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("post_id", "user_id", name="uq_message_read"),
        )
    _create_index_if_missing("ix_message_reads_post_id", "message_reads", ["post_id"])
    _create_index_if_missing("ix_message_reads_user_id", "message_reads", ["user_id"])

    if not _table_exists("template_orders"):
        op.create_table(
            "template_orders",
            sa.Column("template_id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("position", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["template_id"], ["message_templates.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
    _create_index_if_missing("ix_template_orders_user_id", "template_orders", ["user_id"])


def downgrade() -> None:
    for table_name in (
        "template_orders",
        "message_reads",
        "refresh_sessions",
        "message_templates",
        "posts",
        "friend_requests",
        "friendships",
        "users",
    ):
        if _table_exists(table_name):
            op.drop_table(table_name)
