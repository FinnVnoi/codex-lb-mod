"""merge FinnVnoi limit-window and upstream v1.21 migration heads

Revision ID: 20260716_220000_merge_local_and_v121_heads
Revises: 20260712_080000_add_hourly_and_lifetime_limit_windows, 20260713_040000_add_account_refresh_claims
Create Date: 2026-07-16 22:00:00.000000
"""

from __future__ import annotations

revision = "20260716_220000_merge_local_and_v121_heads"
down_revision = (
    "20260712_080000_add_hourly_and_lifetime_limit_windows",
    "20260713_040000_add_account_refresh_claims",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    return


def downgrade() -> None:
    return
