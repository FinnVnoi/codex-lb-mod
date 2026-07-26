from __future__ import annotations

import hmac
import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Header, HTTPException, Security
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.core.auth.dependencies import validate_usage_api_key
from app.core.utils.time import utcnow
from app.db.models import ApiKeyLimit, ApiKeyQuotaPurchase, LimitType, LimitWindow
from app.db.session import get_background_session
from app.modules.api_keys.repository import ApiKeysRepository
from app.modules.api_keys.service import ApiKeyData, ApiKeysService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/quota-shop", tags=["quota-shop"])

PURCHASABLE_TYPES = frozenset({LimitType.TOTAL_TOKENS, LimitType.COST_USD})
MAX_PURCHASE_VALUE = {
    LimitType.TOTAL_TOKENS: 10_000_000_000,
    LimitType.COST_USD: 10_000_000_000,  # microdollars = USD 10,000
}


class QuotaShopRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit_id: int
    limit_type: str
    limit_window: str
    model_filter: str | None = None
    max_value: int
    current_value: int
    remaining_value: int
    reset_at: str
    unit_size: int
    unit_label: str


class QuotaShopCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key_prefix: str
    rules: list[QuotaShopRule]


class QuotaShopFulfillRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_ref: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9:_-]+$")
    api_key: str = Field(min_length=12, max_length=512)
    limit_id: int = Field(gt=0)
    purchased_value: int = Field(gt=0)
    amount_vnd: int = Field(ge=1, le=2_000_000_000)
    limit_type: str
    limit_window: str
    model_filter: str | None = Field(default=None, max_length=100)
    target_reset_at: datetime

    @model_validator(mode="after")
    def validate_type(self) -> "QuotaShopFulfillRequest":
        if self.limit_type not in {LimitType.TOTAL_TOKENS.value, LimitType.COST_USD.value}:
            raise ValueError("Unsupported quota type")
        return self


class QuotaShopFulfillResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    idempotent: bool
    order_ref: str
    key_prefix: str
    limit_id: int
    limit_type: str
    limit_window: str
    model_filter: str | None = None
    purchased_value: int
    amount_vnd: int
    new_max_value: int
    current_value: int
    remaining_value: int
    reset_at: str


def _reset_iso(value: datetime) -> str:
    return value.isoformat() + ("" if value.tzinfo else "Z")


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _rule_unit(limit_type: LimitType) -> tuple[int, str]:
    if limit_type == LimitType.TOTAL_TOKENS:
        return (1_000_000, "1M tokens")
    return (1_000_000, "1 USD")


def _shop_secret() -> str:
    return os.getenv("CODEX_LB_QUOTA_SHOP_SECRET", "").strip()


def _verify_shop_secret(value: str | None) -> None:
    expected = _shop_secret()
    if not expected:
        logger.error("CODEX_LB_QUOTA_SHOP_SECRET is not configured")
        raise HTTPException(status_code=503, detail="Quota shop is not configured")
    if value is None or not hmac.compare_digest(value, expected):
        raise HTTPException(status_code=401, detail="Invalid quota shop secret")


async def _validate_key(raw_key: str) -> ApiKeyData:
    async with get_background_session() as session:
        return await ApiKeysService(ApiKeysRepository(session)).validate_key(raw_key)


@router.get("/catalog", response_model=QuotaShopCatalog)
async def quota_shop_catalog(
    api_key: ApiKeyData = Security(validate_usage_api_key),
) -> QuotaShopCatalog:
    async with get_background_session() as session:
        service = ApiKeysService(ApiKeysRepository(session))
        summary = await service.get_key_usage_summary_for_self(api_key.id)

    if summary is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    rules: list[QuotaShopRule] = []
    for limit in summary.limits:
        try:
            limit_type = LimitType(limit.limit_type)
            LimitWindow(limit.limit_window)
        except ValueError:
            continue
        if limit_type not in PURCHASABLE_TYPES:
            continue
        unit_size, unit_label = _rule_unit(limit_type)
        current = max(0, min(limit.current_value, limit.max_value))
        rules.append(
            QuotaShopRule(
                limit_id=limit.id,
                limit_type=limit.limit_type,
                limit_window=limit.limit_window,
                model_filter=limit.model_filter,
                max_value=limit.max_value,
                current_value=current,
                remaining_value=max(0, limit.max_value - current),
                reset_at=_reset_iso(limit.reset_at),
                unit_size=unit_size,
                unit_label=unit_label,
            )
        )
    return QuotaShopCatalog(key_prefix=api_key.key_prefix, rules=rules)


@router.post("/fulfill", response_model=QuotaShopFulfillResponse)
async def fulfill_quota_purchase(
    payload: QuotaShopFulfillRequest = Body(...),
    x_quota_shop_secret: str | None = Header(default=None),
) -> QuotaShopFulfillResponse:
    _verify_shop_secret(x_quota_shop_secret)

    try:
        limit_type = LimitType(payload.limit_type)
        limit_window = LimitWindow(payload.limit_window)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid limit identity") from exc
    if limit_type not in PURCHASABLE_TYPES:
        raise HTTPException(status_code=400, detail="This limit type cannot be purchased")

    purchased_value = payload.purchased_value
    if purchased_value > MAX_PURCHASE_VALUE[limit_type]:
        raise HTTPException(status_code=400, detail="Purchased quota is too large")

    try:
        api_key = await _validate_key(payload.api_key)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid API key") from exc

    async with get_background_session() as session:
        existing_result = await session.execute(
            select(ApiKeyQuotaPurchase).where(ApiKeyQuotaPurchase.order_ref == payload.order_ref)
        )
        existing = existing_result.scalar_one_or_none()
        if existing is not None:
            if (
                existing.api_key_id != api_key.id
                or existing.limit_id != payload.limit_id
                or existing.limit_type != limit_type.value
                or existing.limit_window != limit_window.value
                or existing.model_filter != payload.model_filter
                or _utc_naive(existing.target_reset_at) != _utc_naive(payload.target_reset_at)
                or existing.purchased_value != purchased_value
                or existing.amount_vnd != payload.amount_vnd
            ):
                raise HTTPException(status_code=409, detail="Order reference was already used for different quota")
            limit = await session.get(ApiKeyLimit, existing.limit_id)
            if limit is None:
                raise HTTPException(status_code=409, detail="Purchased limit no longer exists")
            current = max(0, min(limit.current_value, limit.max_value))
            return QuotaShopFulfillResponse(
                success=True,
                idempotent=True,
                order_ref=existing.order_ref,
                key_prefix=api_key.key_prefix,
                limit_id=limit.id,
                limit_type=limit.limit_type.value,
                limit_window=limit.limit_window.value,
                model_filter=limit.model_filter,
                purchased_value=existing.purchased_value,
                amount_vnd=existing.amount_vnd,
                new_max_value=limit.max_value,
                current_value=current,
                remaining_value=max(0, limit.max_value - current),
                reset_at=_reset_iso(limit.reset_at),
            )

        limit = await session.get(ApiKeyLimit, payload.limit_id)
        if (
            limit is None
            or limit.api_key_id != api_key.id
            or limit.limit_type != limit_type
            or limit.limit_window != limit_window
            or limit.model_filter != payload.model_filter
        ):
            raise HTTPException(status_code=409, detail="The selected limit rule changed; create a new order")

        now = utcnow()
        expected_reset_at = _utc_naive(payload.target_reset_at)
        if _utc_naive(limit.reset_at) != expected_reset_at:
            raise HTTPException(status_code=409, detail="The selected limit window has reset; create a new order")
        if limit.limit_window != LimitWindow.LIFETIME and expected_reset_at <= now:
            raise HTTPException(status_code=409, detail="The selected limit window has reset; create a new order")
        result = await session.execute(
            update(ApiKeyLimit)
            .where(ApiKeyLimit.id == limit.id)
            .where(ApiKeyLimit.api_key_id == api_key.id)
            .where(ApiKeyLimit.reset_at == expected_reset_at)
            .where(ApiKeyLimit.max_value <= MAX_PURCHASE_VALUE[limit_type] - purchased_value)
            .values(max_value=ApiKeyLimit.max_value + purchased_value)
            .returning(ApiKeyLimit.max_value, ApiKeyLimit.current_value, ApiKeyLimit.reset_at)
        )
        updated = result.first()
        if updated is None:
            await session.rollback()
            raise HTTPException(status_code=409, detail="The selected limit changed; retry the purchase")

        session.add(
            ApiKeyQuotaPurchase(
                id=str(uuid.uuid4()),
                order_ref=payload.order_ref,
                api_key_id=api_key.id,
                limit_id=limit.id,
                limit_type=limit_type.value,
                limit_window=limit_window.value,
                model_filter=payload.model_filter,
                purchased_value=purchased_value,
                amount_vnd=payload.amount_vnd,
                target_reset_at=expected_reset_at,
            )
        )
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=409, detail="Order reference is being processed; retry shortly")

        current = max(0, min(int(updated.current_value), int(updated.max_value)))
        return QuotaShopFulfillResponse(
            success=True,
            idempotent=False,
            order_ref=payload.order_ref,
            key_prefix=api_key.key_prefix,
            limit_id=limit.id,
            limit_type=limit_type.value,
            limit_window=limit_window.value,
            model_filter=payload.model_filter,
            purchased_value=purchased_value,
            amount_vnd=payload.amount_vnd,
            new_max_value=int(updated.max_value),
            current_value=current,
            remaining_value=max(0, int(updated.max_value) - current),
            reset_at=_reset_iso(updated.reset_at),
        )
