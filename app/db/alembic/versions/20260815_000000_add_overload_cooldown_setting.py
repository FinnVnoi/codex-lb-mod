"""add configurable upstream overload cooldown

Revision ID: 20260815_000000_add_overload_cooldown_setting
Revises: 20260809_000000_add_prefer_unstarted_quota_accounts
Create Date: 2026-08-15 15:30:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260815_000000_add_overload_cooldown_setting"
down_revision = "20260809_000000_add_prefer_unstarted_quota_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("dashboard_settings")}
    if "overload_cooldown_seconds" not in columns:
        with op.batch_alter_table("dashboard_settings") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "overload_cooldown_seconds",
                    sa.Integer(),
                    nullable=False,
                    server_default="600",
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("dashboard_settings")}
    if "overload_cooldown_seconds" in columns:
        with op.batch_alter_table("dashboard_settings") as batch_op:
            batch_op.drop_column("overload_cooldown_seconds")
