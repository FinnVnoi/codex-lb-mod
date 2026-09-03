"""add logical request retry-chain fields

Revision ID: 20260901_000000_add_logical_retry_chain
Revises: 20260831_010000_add_api_key_logical_requests
"""
import sqlalchemy as sa
from alembic import op

revision = "20260901_000000_add_logical_retry_chain"
down_revision = "20260831_020000_enable_model_source_usage_estimation"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("api_key_logical_requests", sa.Column("conversation_id", sa.String(), nullable=True))
    op.add_column("api_key_logical_requests", sa.Column("useragent_group", sa.String(), nullable=True))
    op.add_column("api_key_logical_requests", sa.Column("superseded_by_id", sa.Integer(), nullable=True))
    op.create_index("idx_logical_retry_match", "api_key_logical_requests", ["api_key_id", "conversation_id", "model", "status", "requested_at"])

def downgrade() -> None:
    op.drop_index("idx_logical_retry_match", table_name="api_key_logical_requests")
    op.drop_column("api_key_logical_requests", "superseded_by_id")
    op.drop_column("api_key_logical_requests", "useragent_group")
    op.drop_column("api_key_logical_requests", "conversation_id")
