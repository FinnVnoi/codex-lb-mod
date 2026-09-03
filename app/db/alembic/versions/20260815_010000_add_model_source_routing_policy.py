"""add model source routing policy

Revision ID: 20260815_010000_add_model_source_routing_policy
Revises: 20260815_000000_add_overload_cooldown_setting
Create Date: 2026-08-15 23:45:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260815_010000_add_model_source_routing_policy"
down_revision = "20260815_000000_add_overload_cooldown_setting"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("model_sources")}
    if "routing_policy" not in columns:
        with op.batch_alter_table("model_sources") as batch_op:
            batch_op.add_column(sa.Column("routing_policy", sa.String(), nullable=False, server_default="normal"))


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("model_sources")}
    if "routing_policy" in columns:
        with op.batch_alter_table("model_sources") as batch_op:
            batch_op.drop_column("routing_policy")
