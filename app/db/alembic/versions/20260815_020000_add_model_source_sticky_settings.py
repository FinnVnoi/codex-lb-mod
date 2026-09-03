"""add model source sticky settings

Revision ID: 20260815_020000_add_model_source_sticky_settings
Revises: 20260815_010000_add_model_source_routing_policy
Create Date: 2026-08-15 23:59:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260815_020000_add_model_source_sticky_settings"
down_revision = "20260815_010000_add_model_source_routing_policy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("dashboard_settings")}
    with op.batch_alter_table("dashboard_settings") as batch_op:
        if "model_source_sticky_enabled" not in columns:
            batch_op.add_column(
                sa.Column("model_source_sticky_enabled", sa.Boolean(), nullable=False, server_default=sa.true())
            )
        if "model_source_sticky_ttl_seconds" not in columns:
            batch_op.add_column(
                sa.Column("model_source_sticky_ttl_seconds", sa.Integer(), nullable=False, server_default="1800")
            )


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("dashboard_settings")}
    with op.batch_alter_table("dashboard_settings") as batch_op:
        if "model_source_sticky_ttl_seconds" in columns:
            batch_op.drop_column("model_source_sticky_ttl_seconds")
        if "model_source_sticky_enabled" in columns:
            batch_op.drop_column("model_source_sticky_enabled")
