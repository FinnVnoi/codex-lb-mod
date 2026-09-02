from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.db.models import ModelSource
from app.db.session import get_background_session
from app.modules.model_sources.repository import ModelSourcesRepository


async def _source_state(source_id: str) -> tuple[int, datetime | None, str | None, str, bool]:
    async with get_background_session() as session:
        row = (await session.execute(select(ModelSource).where(ModelSource.id == source_id))).scalar_one()
        return (
            row.consecutive_auto_pause_failures,
            row.paused_at,
            row.pause_reason,
            row.health_status,
            row.is_enabled,
        )


@pytest.mark.asyncio
async def test_model_source_auto_pauses_after_threshold_and_success_resets(db_setup) -> None:
    source_id = "src_auto_pause_test"
    async with get_background_session() as session:
        session.add(
            ModelSource(
                id=source_id,
                name="auto pause",
                base_url="https://example.test/v1",
                is_enabled=True,
                health_status="unknown",
                paused_at=None,
                pause_reason=None,
                consecutive_auto_pause_failures=0,
                created_at=datetime.now(UTC).replace(tzinfo=None),
                updated_at=datetime.now(UTC).replace(tzinfo=None),
            )
        )
        await session.commit()

    for expected in (1, 2):
        async with get_background_session() as session:
            await ModelSourcesRepository(session).record_auto_pause_result(
                source_id,
                qualifying_failure=True,
                success=False,
                enabled=True,
                threshold=3,
                reason="rate_limit_exceeded",
            )
        failure_count, paused_at, _, _, _ = await _source_state(source_id)
        assert failure_count == expected
        assert paused_at is None

    async with get_background_session() as session:
        await ModelSourcesRepository(session).record_auto_pause_result(
            source_id,
            qualifying_failure=False,
            success=True,
            enabled=True,
            threshold=3,
            reason=None,
        )
    assert (await _source_state(source_id))[0] == 0

    for _ in range(3):
        async with get_background_session() as session:
            await ModelSourcesRepository(session).record_auto_pause_result(
                source_id,
                qualifying_failure=True,
                success=False,
                enabled=True,
                threshold=3,
                reason="api_key_expired",
            )
    failure_count, paused_at, pause_reason, health_status, is_enabled = await _source_state(source_id)
    assert failure_count == 3
    assert is_enabled is True
    assert health_status == "paused"
    assert paused_at is not None
    assert pause_reason == "api_key_expired"
