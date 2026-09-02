from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import case, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload

from app.db.models import ModelSource, ModelSourceModel


class ModelSourcesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_sources(self) -> list[ModelSource]:
        result = await self._session.execute(
            select(ModelSource).options(selectinload(ModelSource.models)).order_by(ModelSource.name)
        )
        return list(result.scalars().unique().all())

    async def list_enabled_sources(self) -> list[ModelSource]:
        result = await self._session.execute(
            select(ModelSource)
            .options(selectinload(ModelSource.models))
            .where(ModelSource.is_enabled.is_(True))
            .where(ModelSource.paused_at.is_(None))
            .order_by(ModelSource.name)
        )
        return list(result.scalars().unique().all())

    async def get_by_id(self, source_id: str) -> ModelSource | None:
        result = await self._session.execute(
            select(ModelSource).options(selectinload(ModelSource.models)).where(ModelSource.id == source_id)
        )
        return result.scalar_one_or_none()

    def _model_source_stmt(
        self,
        model: str,
        *,
        capability_column: InstrumentedAttribute[bool],
        allowed_source_ids: set[str] | None,
        require_streaming: bool,
    ):
        stmt = (
            select(ModelSource)
            .options(selectinload(ModelSource.models))
            .join(ModelSourceModel, ModelSourceModel.source_id == ModelSource.id)
            .where(ModelSource.kind == "openai_compatible")
            .where(ModelSource.is_enabled.is_(True))
            .where(ModelSource.paused_at.is_(None))
            .where(capability_column.is_(True))
            .where(ModelSourceModel.model == model)
            .where(ModelSourceModel.is_enabled.is_(True))
            .order_by(ModelSource.name, ModelSource.id)
        )
        if require_streaming:
            stmt = stmt.where(ModelSourceModel.supports_streaming.is_(True))
        if allowed_source_ids is not None:
            stmt = stmt.where(ModelSource.id.in_(allowed_source_ids))
        return stmt

    async def find_chat_sources_for_model(
        self,
        model: str,
        *,
        allowed_source_ids: set[str] | None = None,
        require_streaming: bool = False,
    ) -> list[ModelSource]:
        if allowed_source_ids is not None and not allowed_source_ids:
            return []
        result = await self._session.execute(
            self._model_source_stmt(
                model,
                capability_column=ModelSource.supports_chat_completions,
                allowed_source_ids=allowed_source_ids,
                require_streaming=require_streaming,
            )
        )
        return list(result.scalars().unique().all())

    async def find_chat_source_for_model(
        self,
        model: str,
        *,
        allowed_source_ids: set[str] | None = None,
        require_streaming: bool = False,
    ) -> ModelSource | None:
        sources = await self.find_chat_sources_for_model(
            model,
            allowed_source_ids=allowed_source_ids,
            require_streaming=require_streaming,
        )
        return sources[0] if sources else None

    async def find_responses_sources_for_model(
        self,
        model: str,
        *,
        allowed_source_ids: set[str] | None = None,
        require_streaming: bool = False,
    ) -> list[ModelSource]:
        if allowed_source_ids is not None and not allowed_source_ids:
            return []
        result = await self._session.execute(
            self._model_source_stmt(
                model,
                capability_column=ModelSource.supports_responses,
                allowed_source_ids=allowed_source_ids,
                require_streaming=require_streaming,
            )
        )
        return list(result.scalars().unique().all())

    async def find_responses_source_for_model(
        self,
        model: str,
        *,
        allowed_source_ids: set[str] | None = None,
        require_streaming: bool = False,
    ) -> ModelSource | None:
        sources = await self.find_responses_sources_for_model(
            model,
            allowed_source_ids=allowed_source_ids,
            require_streaming=require_streaming,
        )
        return sources[0] if sources else None

    async def find_audio_transcriptions_sources_for_model(
        self,
        model: str,
        *,
        allowed_source_ids: set[str] | None = None,
    ) -> list[ModelSource]:
        if allowed_source_ids is not None and not allowed_source_ids:
            return []
        result = await self._session.execute(
            self._model_source_stmt(
                model,
                capability_column=ModelSource.supports_audio_transcriptions,
                allowed_source_ids=allowed_source_ids,
                require_streaming=False,
            )
        )
        return list(result.scalars().unique().all())

    async def find_audio_transcriptions_source_for_model(
        self,
        model: str,
        *,
        allowed_source_ids: set[str] | None = None,
    ) -> ModelSource | None:
        sources = await self.find_audio_transcriptions_sources_for_model(
            model,
            allowed_source_ids=allowed_source_ids,
        )
        return sources[0] if sources else None

    async def create(self, row: ModelSource, *, commit: bool = True) -> ModelSource:
        self._session.add(row)
        if commit:
            await self._session.commit()
            await self._session.refresh(row, attribute_names=["models"])
        return row

    async def delete(self, source_id: str) -> bool:
        result = await self._session.execute(
            select(ModelSource)
            .options(
                selectinload(ModelSource.models),
                selectinload(ModelSource.api_key_assignments),
            )
            .where(ModelSource.id == source_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True

    async def replace_models(
        self,
        source: ModelSource,
        models: list[ModelSourceModel],
        *,
        commit: bool = True,
    ) -> None:
        await self._session.execute(delete(ModelSourceModel).where(ModelSourceModel.source_id == source.id))
        for model in models:
            model.source_id = source.id
            self._session.add(model)
        if commit:
            await self._session.commit()
            await self._session.refresh(source, attribute_names=["models"])

    async def refresh_models(self, source: ModelSource) -> None:
        await self._session.refresh(source, attribute_names=["models"])

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def record_auto_pause_result(
        self,
        source_id: str,
        *,
        qualifying_failure: bool,
        success: bool,
        enabled: bool,
        threshold: int,
        reason: str | None,
    ) -> None:
        """Persist consecutive credential/rate-limit failures for one provider."""
        if success:
            await self._session.execute(
                update(ModelSource)
                .where(ModelSource.id == source_id)
                .values(consecutive_auto_pause_failures=0)
            )
            await self._session.commit()
            return
        if not enabled or not qualifying_failure:
            return
        threshold = max(1, threshold)
        next_count = ModelSource.consecutive_auto_pause_failures + 1
        should_pause = next_count >= threshold
        await self._session.execute(
            update(ModelSource)
            .where(ModelSource.id == source_id, ModelSource.paused_at.is_(None))
            .values(
                consecutive_auto_pause_failures=next_count,
                paused_at=case(
                    (should_pause, datetime.now(UTC).replace(tzinfo=None)),
                    else_=ModelSource.paused_at,
                ),
                pause_reason=case(
                    (should_pause, reason or "provider_auth_or_rate_limit_failure"),
                    else_=ModelSource.pause_reason,
                ),
                health_status=case((should_pause, "paused"), else_=ModelSource.health_status),
            )
        )
        await self._session.commit()
