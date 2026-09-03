"""start API key rolling limit windows on first usage

Revision ID: 20260903_000000_start_limit_on_usage
Revises: 20260902_000000_add_model_source_auto_pause
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260903_000000_start_limit_on_usage"
down_revision = "20260902_000000_add_model_source_auto_pause"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing active cycles keep their deadline. Empty rolling cycles become
    # dormant and receive a deadline atomically on their first reservation.
    with op.batch_alter_table("api_key_limits") as batch:
        batch.alter_column("reset_at", existing_type=sa.DateTime(), nullable=True)
    with op.batch_alter_table("api_key_usage_reservation_items") as batch:
        batch.alter_column("expected_reset_at", existing_type=sa.DateTime(), nullable=True)
    op.execute(
        "UPDATE api_key_limits SET reset_at = NULL "
        "WHERE limit_window != 'lifetime' AND current_value = 0"
    )


def downgrade() -> None:
    # A downgrade cannot recover old dormant anchors; start them from now.
    op.execute(
        "UPDATE api_key_limits SET reset_at = CURRENT_TIMESTAMP "
        "WHERE reset_at IS NULL"
    )
    op.execute(
        "UPDATE api_key_usage_reservation_items SET expected_reset_at = CURRENT_TIMESTAMP "
        "WHERE expected_reset_at IS NULL"
    )
    with op.batch_alter_table("api_key_usage_reservation_items") as batch:
        batch.alter_column("expected_reset_at", existing_type=sa.DateTime(), nullable=False)
    with op.batch_alter_table("api_key_limits") as batch:
        batch.alter_column("reset_at", existing_type=sa.DateTime(), nullable=False)
