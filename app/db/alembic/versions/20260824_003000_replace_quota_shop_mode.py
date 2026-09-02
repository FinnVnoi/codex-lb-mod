"""replace per-limit shop switches with per-key quota shop mode

Revision ID: 20260824_003000_replace_quota_shop_mode
Revises: 20260824_000000_add_quota_shop_controls
"""
from __future__ import annotations
import sqlalchemy as sa
from alembic import op

revision = "20260824_003000_replace_quota_shop_mode"
down_revision = "20260824_000000_add_quota_shop_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("api_keys")}
    with op.batch_alter_table("api_keys") as b:
        if "quota_shop_enabled" not in cols:
            b.add_column(sa.Column("quota_shop_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
        if "quota_shop_max_windows" not in cols:
            b.add_column(sa.Column("quota_shop_max_windows", sa.Integer(), nullable=False, server_default="1"))
        if "quota_shop_options" not in cols:
            b.add_column(sa.Column("quota_shop_options", sa.Text(), nullable=False, server_default='[{"limit_type":"total_tokens","limit_window":"lifetime"},{"limit_type":"cost_usd","limit_window":"lifetime"}]'))
        if "quota_shop_max_purchases" in cols:
            b.drop_column("quota_shop_max_purchases")
    limit_cols = {c["name"] for c in sa.inspect(bind).get_columns("api_key_limits")}
    if "quota_shop_enabled" in limit_cols:
        with op.batch_alter_table("api_key_limits") as b:
            b.drop_column("quota_shop_enabled")


def downgrade() -> None:
    bind = op.get_bind()
    with op.batch_alter_table("api_keys") as b:
        b.add_column(sa.Column("quota_shop_max_purchases", sa.Integer(), nullable=True))
    with op.batch_alter_table("api_key_limits") as b:
        b.add_column(sa.Column("quota_shop_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
