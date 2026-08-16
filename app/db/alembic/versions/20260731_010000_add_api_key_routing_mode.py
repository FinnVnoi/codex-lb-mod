"""add mixed account/provider routing mode to API keys

Revision ID: 20260731_010000_add_api_key_routing_mode
Revises: 20260731_000000_add_model_source_upstream_model
Create Date: 2026-07-31 23:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260731_010000_add_api_key_routing_mode"
down_revision = "20260731_000000_add_model_source_upstream_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("api_keys")}
    if "routing_mode" not in columns:
        with op.batch_alter_table("api_keys") as batch_op:
            batch_op.add_column(
                sa.Column("routing_mode", sa.String(), nullable=False, server_default="balanced")
            )


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("api_keys")}
    if "routing_mode" in columns:
        with op.batch_alter_table("api_keys") as batch_op:
            batch_op.drop_column("routing_mode")
