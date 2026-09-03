"""Add routing preference for accounts with unstarted quota countdowns.

Revision ID: 20260809_000000_add_prefer_unstarted_quota_accounts
Revises: 20260808_000000_add_prefer_earlier_renewal_accounts
Create Date: 2026-08-09 10:40:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260809_000000_add_prefer_unstarted_quota_accounts"
down_revision: str | Sequence[str] | None = "20260808_000000_add_prefer_earlier_renewal_accounts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "dashboard_settings",
        sa.Column(
            "prefer_unstarted_quota_accounts",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "dashboard_settings",
        sa.Column(
            "prefer_unstarted_quota_window",
            sa.String(),
            nullable=False,
            server_default=sa.text("'both'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("dashboard_settings", "prefer_unstarted_quota_window")
    op.drop_column("dashboard_settings", "prefer_unstarted_quota_accounts")
