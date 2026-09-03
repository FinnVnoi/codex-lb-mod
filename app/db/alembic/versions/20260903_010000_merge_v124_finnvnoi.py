"""merge upstream v1.24 and FinnVnoi migration heads

Revision ID: 20260903_010000_merge_v124_finnvnoi
Revises: 20260816_000000_add_model_source_embeddings,
         20260903_000000_start_limit_on_usage
"""
from __future__ import annotations

revision = "20260903_010000_merge_v124_finnvnoi"
down_revision = (
    "20260816_000000_add_model_source_embeddings",
    "20260903_000000_start_limit_on_usage",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
