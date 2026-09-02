"""add model source auto-pause state and settings

Revision ID: 20260902_000000_add_model_source_auto_pause
Revises: 20260901_000000_add_logical_retry_chain
"""
import sqlalchemy as sa
from alembic import op

revision = "20260902_000000_add_model_source_auto_pause"
down_revision = "20260901_000000_add_logical_retry_chain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("model_sources", sa.Column("paused_at", sa.DateTime(), nullable=True))
    op.add_column("model_sources", sa.Column("pause_reason", sa.String(), nullable=True))
    op.add_column(
        "model_sources",
        sa.Column("consecutive_auto_pause_failures", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "dashboard_settings",
        sa.Column("model_source_auto_pause_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "dashboard_settings",
        sa.Column("model_source_auto_pause_threshold", sa.Integer(), nullable=False, server_default="3"),
    )


def downgrade() -> None:
    op.drop_column("dashboard_settings", "model_source_auto_pause_threshold")
    op.drop_column("dashboard_settings", "model_source_auto_pause_enabled")
    op.drop_column("model_sources", "consecutive_auto_pause_failures")
    op.drop_column("model_sources", "pause_reason")
    op.drop_column("model_sources", "paused_at")
