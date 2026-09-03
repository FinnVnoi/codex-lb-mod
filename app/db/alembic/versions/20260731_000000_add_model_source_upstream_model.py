"""add upstream model aliases for OpenAI-compatible sources

Revision ID: 20260731_000000_add_model_source_upstream_model
Revises: 20260725_000000_merge_quota_shop_and_v122_heads
Create Date: 2026-07-31 22:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

revision = "20260731_000000_add_model_source_upstream_model"
down_revision = "20260725_000000_merge_quota_shop_and_v122_heads"
branch_labels = None
depends_on = None


def _columns(connection: Connection, table_name: str) -> set[str]:
    if not sa.inspect(connection).has_table(table_name):
        return set()
    return {column["name"] for column in sa.inspect(connection).get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind, "model_source_models")
    if columns and "upstream_model" not in columns:
        with op.batch_alter_table("model_source_models") as batch_op:
            batch_op.add_column(sa.Column("upstream_model", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    if "upstream_model" in _columns(bind, "model_source_models"):
        with op.batch_alter_table("model_source_models") as batch_op:
            batch_op.drop_column("upstream_model")
