"""enable model source missing usage estimation by default

Revision ID: 20260831_020000_enable_model_source_usage_estimation
Revises: 20260831_010000_add_api_key_logical_requests
Create Date: 2026-08-31 21:27:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260831_020000_enable_model_source_usage_estimation"
down_revision = "20260831_010000_add_api_key_logical_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("model_sources")}
    if "estimate_missing_stream_usage" not in columns:
        return
    op.execute(sa.text("UPDATE model_sources SET estimate_missing_stream_usage = true"))
    with op.batch_alter_table("model_sources") as batch_op:
        batch_op.alter_column(
            "estimate_missing_stream_usage",
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        )


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("model_sources")}
    if "estimate_missing_stream_usage" not in columns:
        return
    with op.batch_alter_table("model_sources") as batch_op:
        batch_op.alter_column(
            "estimate_missing_stream_usage",
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        )
