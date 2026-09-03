"""add earlier subscription renewal routing preference

Revision ID: 20260808_000000_add_prefer_earlier_renewal_accounts
Revises: 20260731_010000_add_api_key_routing_mode
Create Date: 2026-08-08 15:50:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260808_000000_add_prefer_earlier_renewal_accounts"
down_revision = "20260731_010000_add_api_key_routing_mode"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("dashboard_settings")}
    if "prefer_earlier_renewal_accounts" not in columns:
        with op.batch_alter_table("dashboard_settings") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "prefer_earlier_renewal_accounts",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("dashboard_settings")}
    if "prefer_earlier_renewal_accounts" in columns:
        with op.batch_alter_table("dashboard_settings") as batch_op:
            batch_op.drop_column("prefer_earlier_renewal_accounts")
