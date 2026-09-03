"""add hourly and lifetime API key limit windows

Revision ID: 20260712_080000_add_hourly_and_lifetime_limit_windows
Revises: 20260611_000000_merge_dashboard_guest_and_weekly_useragent_heads
Create Date: 2026-07-12 08:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260712_080000_add_hourly_and_lifetime_limit_windows"
down_revision = "20260611_000000_merge_dashboard_guest_and_weekly_useragent_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql" or not sa.inspect(bind).has_table("api_key_limits"):
        return

    op.execute(sa.text("ALTER TYPE limit_window ADD VALUE IF NOT EXISTS '1h'"))
    op.execute(sa.text("ALTER TYPE limit_window ADD VALUE IF NOT EXISTS 'lifetime'"))


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    return
