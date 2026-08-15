"""作成日時カラムをモデル定義と一致させる。

Revision ID: 20260816_0002
Revises: 20260816_0001
Create Date: 2026-08-16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260816_0002"
down_revision = "20260816_0001"
branch_labels = None
depends_on = None


def _is_nullable(table_name: str, column_name: str) -> bool:
    columns = sa.inspect(op.get_bind()).get_columns(table_name)
    return next(column["nullable"] for column in columns if column["name"] == column_name)


def upgrade() -> None:
    for table_name in ("posts", "message_templates"):
        if _is_nullable(table_name, "created_at"):
            op.execute(
                sa.text(
                    f"UPDATE {table_name} SET created_at = CURRENT_TIMESTAMP "
                    "WHERE created_at IS NULL"
                )
            )
            with op.batch_alter_table(table_name) as batch_op:
                batch_op.alter_column(
                    "created_at",
                    existing_type=sa.DateTime(),
                    nullable=False,
                )


def downgrade() -> None:
    for table_name in ("message_templates", "posts"):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DateTime(),
                nullable=True,
            )
