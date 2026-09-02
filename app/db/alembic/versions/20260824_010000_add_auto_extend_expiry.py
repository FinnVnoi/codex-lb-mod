"""add daily API key expiry auto-extension settings

Revision ID: 20260824_010000_add_auto_extend_expiry
Revises: 20260824_003000_replace_quota_shop_mode
"""
from __future__ import annotations
import sqlalchemy as sa
from alembic import op

revision = "20260824_010000_add_auto_extend_expiry"
down_revision = "20260824_003000_replace_quota_shop_mode"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("api_keys")}
    with op.batch_alter_table("api_keys") as b:
        if "auto_extend_expiry" not in cols:
            b.add_column(sa.Column("auto_extend_expiry", sa.Boolean(), nullable=False, server_default=sa.false()))
        if "auto_extend_expiry_type" not in cols:
            b.add_column(sa.Column("auto_extend_expiry_type", sa.String(32), nullable=True))
        if "auto_extend_expiry_threshold" not in cols:
            b.add_column(sa.Column("auto_extend_expiry_threshold", sa.BigInteger(), nullable=True))
        if "auto_extend_expiry_last_processed_date" not in cols:
            b.add_column(sa.Column("auto_extend_expiry_last_processed_date", sa.Date(), nullable=True))

def downgrade() -> None:
    with op.batch_alter_table("api_keys") as b:
        for name in ("auto_extend_expiry_last_processed_date", "auto_extend_expiry_threshold", "auto_extend_expiry_type", "auto_extend_expiry"):
            b.drop_column(name)
