from __future__ import annotations
import asyncio
from datetime import timedelta
from sqlalchemy import case, delete, func, select
from app.db.models import ApiKey, ApiKeyLogicalRequest, RequestLog
from app.db.session import get_background_session, sqlite_writer_section

async def main() -> None:
    async with get_background_session() as session:
        logical_id = func.coalesce(RequestLog.archive_request_id, RequestLog.request_id)
        grouped = (select(
            RequestLog.api_key_id.label('api_key_id'), logical_id.label('logical_id'),
            func.max(RequestLog.conversation_id).label('conversation_id'), func.max(RequestLog.useragent_group).label('useragent_group'),
            func.max(RequestLog.requested_at).label('requested_at'),
            func.max(case((RequestLog.status.in_(('ok', 'success')), 1), else_=0)).label('has_success'),
            func.max(RequestLog.id).label('last_id'),
            func.max(case((RequestLog.status.in_(('ok', 'success')), RequestLog.id), else_=None)).label('success_id'),
            func.coalesce(func.sum(RequestLog.input_tokens), 0).label('input_tokens'),
            func.coalesce(func.sum(func.coalesce(RequestLog.output_tokens, RequestLog.reasoning_tokens, 0)), 0).label('output_tokens'),
            func.coalesce(func.sum(RequestLog.cached_input_tokens), 0).label('cached_input_tokens'),
            func.coalesce(func.sum(RequestLog.cost_usd), 0.0).label('total_cost_usd'),
        ).where(RequestLog.api_key_id.in_(select(ApiKey.id)), RequestLog.request_kind.not_in(('warmup','limit_warmup')))
         .group_by(RequestLog.api_key_id, logical_id).subquery())
        terminal_id = case((grouped.c.has_success == 1, grouped.c.success_id), else_=grouped.c.last_id)
        rows = (await session.execute(select(grouped, RequestLog.model, RequestLog.status, RequestLog.error_code).join(RequestLog, RequestLog.id == terminal_id))).all()
        async with sqlite_writer_section():
            await session.execute(delete(ApiKeyLogicalRequest))
            session.add_all([ApiKeyLogicalRequest(
                api_key_id=r.api_key_id, logical_id=r.logical_id, conversation_id=r.conversation_id, useragent_group=r.useragent_group, requested_at=r.requested_at, model=r.model,
                status='success' if r.has_success else ('cancelled' if r.status == 'cancelled' else 'error'),
                error_code=None if r.has_success else r.error_code, input_tokens=int(r.input_tokens or 0),
                output_tokens=int(r.output_tokens or 0), cached_input_tokens=int(r.cached_input_tokens or 0),
                total_cost_usd=float(r.total_cost_usd or 0.0),
            ) for r in rows])
            await session.flush()
            retryable = ('insufficient_quota','rate_limit_exceeded','model_source_unavailable','overloaded')
            ordered = (await session.execute(select(ApiKeyLogicalRequest).order_by(ApiKeyLogicalRequest.api_key_id, ApiKeyLogicalRequest.requested_at, ApiKeyLogicalRequest.id))).scalars().all()
            pending = {}
            superseded = 0
            for row in ordered:
                key = (row.api_key_id, row.conversation_id, row.model)
                if row.status == 'error' and row.error_code in retryable and row.conversation_id and row.input_tokens == 0 and row.output_tokens == 0 and row.total_cost_usd == 0:
                    pending[key] = row
                elif row.status == 'success' and row.conversation_id:
                    previous = pending.get(key)
                    if previous and timedelta(0) <= row.requested_at - previous.requested_at <= timedelta(seconds=30):
                        previous.superseded_by_id = row.id; superseded += 1
                    pending.pop(key, None)
            await session.commit()
        print(f'backfilled {len(rows)} logical requests; superseded {superseded} retry errors')

if __name__ == '__main__': asyncio.run(main())
