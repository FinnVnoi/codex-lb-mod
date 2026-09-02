"""add durable api key logical requests

Revision ID: 20260831_010000_add_api_key_logical_requests
Revises: 20260831_000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20260831_010000_add_api_key_logical_requests"
down_revision = "20260831_000000_add_model_source_usage_estimation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_key_logical_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("api_key_id", sa.String(), nullable=False),
        sa.Column("logical_id", sa.String(), nullable=False),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_code", sa.String(), nullable=True),
        sa.Column("input_tokens", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("output_tokens", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("cached_input_tokens", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("total_cost_usd", sa.Float(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["api_key_id"], ["api_keys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("api_key_id", "logical_id", name="uq_api_key_logical_request"),
    )
    op.create_index("idx_api_key_logical_requests_key_time", "api_key_logical_requests", ["api_key_id", "requested_at", "id"])


def downgrade() -> None:
    op.drop_index("idx_api_key_logical_requests_key_time", table_name="api_key_logical_requests")
    op.drop_table("api_key_logical_requests")
