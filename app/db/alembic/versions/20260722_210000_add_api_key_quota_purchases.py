"""add API key paid quota purchase ledger

Revision ID: 20260722_210000_add_api_key_quota_purchases
Revises: 20260716_220000_merge_local_and_v121_heads
Create Date: 2026-07-22 21:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260722_210000_add_api_key_quota_purchases"
down_revision = "20260716_220000_merge_local_and_v121_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("api_key_quota_purchases"):
        return
    op.create_table(
        "api_key_quota_purchases",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("order_ref", sa.String(length=128), nullable=False),
        sa.Column("api_key_id", sa.String(), nullable=False),
        sa.Column("limit_id", sa.Integer(), nullable=False),
        sa.Column("limit_type", sa.String(length=32), nullable=False),
        sa.Column("limit_window", sa.String(length=32), nullable=False),
        sa.Column("model_filter", sa.String(length=100), nullable=True),
        sa.Column("purchased_value", sa.BigInteger(), nullable=False),
        sa.Column("amount_vnd", sa.BigInteger(), nullable=False),
        sa.Column("target_reset_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["api_key_id"], ["api_keys.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["limit_id"], ["api_key_limits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_api_key_quota_purchases_order_ref",
        "api_key_quota_purchases",
        ["order_ref"],
        unique=True,
    )
    op.create_index(
        "ix_api_key_quota_purchases_api_key_id",
        "api_key_quota_purchases",
        ["api_key_id"],
    )
    op.create_index(
        "ix_api_key_quota_purchases_limit_id",
        "api_key_quota_purchases",
        ["limit_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("api_key_quota_purchases"):
        return
    op.drop_index("ix_api_key_quota_purchases_limit_id", table_name="api_key_quota_purchases")
    op.drop_index("ix_api_key_quota_purchases_api_key_id", table_name="api_key_quota_purchases")
    op.drop_index("ix_api_key_quota_purchases_order_ref", table_name="api_key_quota_purchases")
    op.drop_table("api_key_quota_purchases")
