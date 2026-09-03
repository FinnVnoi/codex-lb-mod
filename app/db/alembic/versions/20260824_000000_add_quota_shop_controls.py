"""add per-key quota-shop controls

Revision ID: 20260824_000000_add_quota_shop_controls
Revises: 20260817_000000_add_dashboard_routing_settings
Create Date: 2026-08-24 01:20:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260824_000000_add_quota_shop_controls"
down_revision = "20260817_000000_add_dashboard_routing_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    key_columns = {column["name"] for column in sa.inspect(bind).get_columns("api_keys")}
    if "quota_shop_max_purchases" not in key_columns:
        with op.batch_alter_table("api_keys") as batch_op:
            batch_op.add_column(sa.Column("quota_shop_max_purchases", sa.Integer(), nullable=True))

    limit_columns = {column["name"] for column in sa.inspect(bind).get_columns("api_key_limits")}
    if "quota_shop_enabled" not in limit_columns:
        with op.batch_alter_table("api_key_limits") as batch_op:
            batch_op.add_column(
                sa.Column("quota_shop_enabled", sa.Boolean(), nullable=False, server_default=sa.false())
            )


def downgrade() -> None:
    bind = op.get_bind()
    limit_columns = {column["name"] for column in sa.inspect(bind).get_columns("api_key_limits")}
    if "quota_shop_enabled" in limit_columns:
        with op.batch_alter_table("api_key_limits") as batch_op:
            batch_op.drop_column("quota_shop_enabled")

    key_columns = {column["name"] for column in sa.inspect(bind).get_columns("api_keys")}
    if "quota_shop_max_purchases" in key_columns:
        with op.batch_alter_table("api_keys") as batch_op:
            batch_op.drop_column("quota_shop_max_purchases")
