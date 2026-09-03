from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

pytestmark = pytest.mark.unit


MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "app/db/alembic/versions/20260817_000000_add_dashboard_routing_settings.py"
)


def _load_migration():
    spec = importlib.util.spec_from_file_location("routing_settings_migration", MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dashboard_routing_settings_migration_defaults_existing_rows() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    metadata = sa.MetaData()
    table = sa.Table(
        "dashboard_settings",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sticky_threads_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(table.insert().values(id=1, sticky_threads_enabled=True))
        context = MigrationContext.configure(conn)
        op = Operations(context)
        module = _load_migration()
        original_op = module.op
        module.op = op
        try:
            module.upgrade()
        finally:
            module.op = original_op

        row = conn.execute(sa.text("SELECT * FROM dashboard_settings WHERE id = 1")).mappings().one()

    assert row["global_api_routing_override"] == "normal"
    assert row["provider_failure_policy"] == "account_after_first_failure"
    assert row["account_failure_policy"] == "accounts_before_providers"
    assert row["provider_max_attempts"] == 3
    assert row["account_max_attempts"] == 3
