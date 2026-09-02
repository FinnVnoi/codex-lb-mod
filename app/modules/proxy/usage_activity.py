from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApiKeyLogicalRequest

UsageWindow = Literal["1d", "7d", "30d", "lt"]

@dataclass(frozen=True, slots=True)
class LogicalUsageTotals:
    request_count: int
    total_tokens: int
    cached_input_tokens: int
    total_cost_usd: float

@dataclass(frozen=True, slots=True)
class LogicalUsageRow:
    id: int
    requested_at: datetime
    model: str
    status: str
    error_code: str | None
    total_tokens: int
    cached_input_tokens: int
    cost_usd: float

def _since(window: UsageWindow, now: datetime) -> datetime | None:
    return {"1d": now-timedelta(days=1), "7d": now-timedelta(days=7), "30d": now-timedelta(days=30), "lt": None}[window]

async def get_logical_usage(
    session: AsyncSession, *, api_key_id: str, window: UsageWindow,
    include_logs: bool, after_id: int | None, page_size: int = 10, now: datetime,
) -> tuple[LogicalUsageTotals, list[LogicalUsageRow], int, int, int | None, list[int]]:
    total_conditions = [ApiKeyLogicalRequest.api_key_id == api_key_id, ApiKeyLogicalRequest.superseded_by_id.is_(None)]
    since = _since(window, now)
    if since is not None:
        total_conditions.append(ApiKeyLogicalRequest.requested_at >= since)
    totals_row = (await session.execute(select(
        func.count().label("request_count"),
        func.coalesce(func.sum(ApiKeyLogicalRequest.input_tokens + ApiKeyLogicalRequest.output_tokens), 0).label("total_tokens"),
        func.coalesce(func.sum(ApiKeyLogicalRequest.cached_input_tokens), 0).label("cached_input_tokens"),
        func.coalesce(func.sum(ApiKeyLogicalRequest.total_cost_usd), 0.0).label("total_cost_usd"),
    ).where(*total_conditions))).one()
    log_count = int((await session.execute(select(func.count()).where(ApiKeyLogicalRequest.api_key_id == api_key_id, ApiKeyLogicalRequest.superseded_by_id.is_(None)))).scalar_one())
    latest_id = (await session.execute(select(func.max(ApiKeyLogicalRequest.id)).where(ApiKeyLogicalRequest.api_key_id == api_key_id))).scalar_one()
    total_pages = max(1, (log_count + page_size - 1) // page_size)
    rows: list[LogicalUsageRow] = []
    if include_logs:
        log_conditions = [ApiKeyLogicalRequest.api_key_id == api_key_id, ApiKeyLogicalRequest.superseded_by_id.is_(None)]
        if after_id is not None:
            log_conditions.append(ApiKeyLogicalRequest.id > after_id)
        query = select(ApiKeyLogicalRequest).where(*log_conditions).order_by(
            ApiKeyLogicalRequest.requested_at.desc(), ApiKeyLogicalRequest.id.desc()
        )
        items = (await session.execute(query)).scalars().all()
        rows = [LogicalUsageRow(
            id=row.id, requested_at=row.requested_at, model=row.model, status=row.status,
            error_code=row.error_code if row.status != "success" else None,
            total_tokens=row.input_tokens + row.output_tokens,
            cached_input_tokens=row.cached_input_tokens, cost_usd=row.total_cost_usd,
        ) for row in items]
    removed_ids: list[int] = []
    if after_id is not None:
        removed_ids = [int(value) for value in (await session.execute(
            select(ApiKeyLogicalRequest.id).where(
                ApiKeyLogicalRequest.api_key_id == api_key_id,
                ApiKeyLogicalRequest.superseded_by_id > after_id,
            )
        )).scalars().all()]
    return LogicalUsageTotals(
        request_count=int(totals_row.request_count or 0), total_tokens=int(totals_row.total_tokens or 0),
        cached_input_tokens=int(totals_row.cached_input_tokens or 0), total_cost_usd=float(totals_row.total_cost_usd or 0.0),
    ), rows, total_pages, log_count, int(latest_id) if latest_id is not None else None, removed_ids
