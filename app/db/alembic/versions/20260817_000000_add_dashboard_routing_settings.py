"""add dashboard routing settings

Revision ID: 20260817_000000_add_dashboard_routing_settings
Revises: 20260815_020000_add_model_source_sticky_settings
Create Date: 2026-08-17 22:30:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260817_000000_add_dashboard_routing_settings"
down_revision = "20260815_020000_add_model_source_sticky_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("dashboard_settings")}
    with op.batch_alter_table("dashboard_settings") as batch_op:
        if "global_api_routing_override" not in columns:
            batch_op.add_column(
                sa.Column(
                    "global_api_routing_override",
                    sa.String(),
                    nullable=False,
                    server_default="normal",
                )
            )
        if "provider_failure_policy" not in columns:
            batch_op.add_column(
                sa.Column(
                    "provider_failure_policy",
                    sa.String(),
                    nullable=False,
                    server_default="account_after_first_failure",
                )
            )
        if "account_failure_policy" not in columns:
            batch_op.add_column(
                sa.Column(
                    "account_failure_policy",
                    sa.String(),
                    nullable=False,
                    server_default="accounts_before_providers",
                )
            )
        if "provider_max_attempts" not in columns:
            batch_op.add_column(
                sa.Column("provider_max_attempts", sa.Integer(), nullable=False, server_default="3")
            )
        if "account_max_attempts" not in columns:
            batch_op.add_column(sa.Column("account_max_attempts", sa.Integer(), nullable=False, server_default="3"))


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("dashboard_settings")}
    with op.batch_alter_table("dashboard_settings") as batch_op:
        if "account_max_attempts" in columns:
            batch_op.drop_column("account_max_attempts")
        if "provider_max_attempts" in columns:
            batch_op.drop_column("provider_max_attempts")
        if "account_failure_policy" in columns:
            batch_op.drop_column("account_failure_policy")
        if "provider_failure_policy" in columns:
            batch_op.drop_column("provider_failure_policy")
        if "global_api_routing_override" in columns:
            batch_op.drop_column("global_api_routing_override")
