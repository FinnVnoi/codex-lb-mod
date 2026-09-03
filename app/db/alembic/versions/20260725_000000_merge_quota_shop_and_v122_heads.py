"""merge FinnVnoi quota-shop and upstream v1.22 migration heads

Revision ID: 20260725_000000_merge_quota_shop_and_v122_heads
Revises:
- 20260722_210000_add_api_key_quota_purchases
- 20260722_000000_backfill_request_log_useragent_families
Create Date: 2026-07-25 00:00:00.000000
"""

from __future__ import annotations

revision = "20260725_000000_merge_quota_shop_and_v122_heads"
down_revision = (
    "20260722_210000_add_api_key_quota_purchases",
    "20260722_000000_backfill_request_log_useragent_families",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    return


def downgrade() -> None:
    return
