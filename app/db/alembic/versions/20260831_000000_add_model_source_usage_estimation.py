"""add model source missing usage estimation

Revision ID: 20260831_000000_add_model_source_usage_estimation
Revises: 20260824_010000_add_auto_extend_expiry
Create Date: 2026-08-31 20:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260831_000000_add_model_source_usage_estimation"
down_revision = "20260824_010000_add_auto_extend_expiry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("model_sources")}
    if "estimate_missing_stream_usage" not in columns:
        with op.batch_alter_table("model_sources") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "estimate_missing_stream_usage",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("model_sources")}
    if "estimate_missing_stream_usage" in columns:
        with op.batch_alter_table("model_sources") as batch_op:
            batch_op.drop_column("estimate_missing_stream_usage")
