from __future__ import annotations

import hashlib
import hmac
import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Header, HTTPException, Security
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from app.core.auth.api_key_cache import get_api_key_cache
from app.core.auth.dependencies import validate_usage_api_key
from app.core.cache.invalidation import NAMESPACE_API_KEY, get_cache_invalidation_poller
from app.core.utils.time import utcnow
from app.db.models import ApiKey, ApiKeyLimit, ApiKeyQuotaPurchase, LimitType, LimitWindow
from app.db.session import get_background_session
from app.modules.api_keys.limit_windows import next_limit_reset
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
    quota_shop_enabled: bool = False
    expires_at: str | None = None
    expiry_enforced: bool = False
    max_windows: int = 1
    windows_used: int = 0
    windows_remaining: int = 1
    can_purchase: bool = True
    rules: list[QuotaShopRule]


class QuotaShopFulfillRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_ref: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9:_-]+$")
    api_key: str = Field(min_length=12, max_length=512)
    limit_id: int = Field(ge=0)
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


def _shop_key_prefix(value: str) -> str:
    value = value.strip()
    return value[:12] + "..." if len(value) > 12 else value


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
        purchased_limit_ids = set(
            (
                await session.execute(
                    select(ApiKeyQuotaPurchase.limit_id).where(
                        ApiKeyQuotaPurchase.api_key_id == api_key.id,
                        (ApiKeyQuotaPurchase.order_ref.like("SHOP:%") | ApiKeyQuotaPurchase.order_ref.like("AQ:%")),
                    )
                )
            )
            .scalars()
            .all()
        )

    if summary is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    rules: list[QuotaShopRule] = []
    # Quota Shop Mode is optional. Without it, keep selling existing
    # purchasable limits normally; only enabled mode uses the admin catalog.
    options = (
        api_key.quota_shop_options
        if api_key.quota_shop_enabled
        else [
            {"limit_type": x.limit_type, "limit_window": x.limit_window, "model_filter": x.model_filter}
            for x in summary.limits
            if x.limit_type in {item.value for item in PURCHASABLE_TYPES}
        ]
    )
    for option in options:
        try:
            limit_type = LimitType(str(option["limit_type"]))
            limit_window = LimitWindow(str(option["limit_window"]))
            option_model = option.get("model_filter")
        except (KeyError, ValueError, TypeError):
            continue
        if limit_type not in PURCHASABLE_TYPES:
            continue
        existing = next(
            (
                x
                for x in summary.limits
                if x.limit_type == limit_type.value
                and x.limit_window == limit_window.value
                and x.model_filter == option_model
            ),
            None,
        )
        if existing is None and limit_window == LimitWindow.WEEKLY and limit_type == LimitType.COST_USD:
            existing = next(
                (
                    x
                    for x in summary.limits
                    if x.limit_type == limit_type.value and x.limit_window == limit_window.value
                ),
                None,
            )
        unit_size, unit_label = _rule_unit(limit_type)
        current = max(0, min(existing.current_value, existing.max_value)) if existing else 0
        rules.append(
            QuotaShopRule(
                limit_id=existing.id if existing else 0,
                limit_type=limit_type.value,
                limit_window=limit_window.value,
                model_filter=option_model,
                max_value=existing.max_value if existing else 0,
                current_value=current,
                remaining_value=max(0, (existing.max_value - current) if existing else 0),
                # A dormant window has no enforcement countdown yet. The shop still
                # needs a concrete order snapshot, so quote a window starting now.
                reset_at=_reset_iso(
                    existing.reset_at
                    if existing is not None and existing.reset_at is not None
                    else next_limit_reset(utcnow(), limit_window)
                ),
                unit_size=unit_size,
                unit_label=unit_label,
            )
        )
    # Fixed admin limits do not consume the customer's shop-window allowance.
    # A window counts only after a paid fulfillment created/used it.
    windows_used = (
        len({x.limit_id for x in rules if x.limit_id and x.limit_id in purchased_limit_ids})
        if api_key.quota_shop_enabled
        else 0
    )
    return QuotaShopCatalog(
        key_prefix=_shop_key_prefix(api_key.key_prefix),
        quota_shop_enabled=api_key.quota_shop_enabled,
        expires_at=_reset_iso(api_key.expires_at) if api_key.expires_at is not None else None,
        expiry_enforced=api_key.expires_at is not None,
        max_windows=api_key.quota_shop_max_windows,
        windows_used=windows_used,
        windows_remaining=max(0, api_key.quota_shop_max_windows - windows_used),
        can_purchase=bool(rules),
        rules=rules,
    )


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
                # A first-time option is ordered with limit_id=0. Fulfillment
                # creates the real limit, so retries must match by identity
                # rather than reject the newly assigned database id.
                or (payload.limit_id != 0 and existing.limit_id != payload.limit_id)
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
                key_prefix=_shop_key_prefix(api_key.key_prefix),
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

        now = utcnow()
        expected_reset_at = _utc_naive(payload.target_reset_at)
        mode_was_enabled = api_key.quota_shop_enabled
        limit = await session.get(ApiKeyLimit, payload.limit_id)
        if (
            limit is None
            or limit.api_key_id != api_key.id
            or limit.limit_type != limit_type
            or limit.limit_window != limit_window
            or limit.model_filter != payload.model_filter
        ):
            # A missing limit is created by the first purchase only in explicit
            # Quota Shop Mode. Otherwise the ordinary shop needs an existing limit.
            if limit is None and api_key.quota_shop_enabled:
                options = {
                    (str(x.get("limit_type")), str(x.get("limit_window")), x.get("model_filter"))
                    for x in api_key.quota_shop_options
                }
                if (limit_type.value, limit_window.value, payload.model_filter) not in options:
                    raise HTTPException(status_code=409, detail="This quota option is not available in the shop")
                existing_windows = await session.execute(
                    select(ApiKeyLimit.id).where(ApiKeyLimit.api_key_id == api_key.id)
                )
                if len(existing_windows.all()) >= api_key.quota_shop_max_windows:
                    raise HTTPException(status_code=409, detail="Maximum quota windows reached")
                limit = ApiKeyLimit(
                    api_key_id=api_key.id,
                    limit_type=limit_type,
                    limit_window=limit_window,
                    max_value=0,
                    current_value=0,
                    model_filter=payload.model_filter,
                    reset_at=expected_reset_at,
                )
                session.add(limit)
                await session.flush()
            if limit is None:
                raise HTTPException(status_code=409, detail="The selected quota option is invalid")
        if limit is None:
            raise HTTPException(status_code=409, detail="The selected quota option is invalid")
        if api_key.quota_shop_enabled:
            options = {
                (str(x.get("limit_type")), str(x.get("limit_window")), x.get("model_filter"))
                for x in api_key.quota_shop_options
            }
            allowed = (limit_type.value, limit_window.value, payload.model_filter) in options
        else:
            allowed = limit is not None and limit.api_key_id == api_key.id
        if not allowed:
            raise HTTPException(status_code=409, detail="This quota option is not available in the shop")

        dormant_window = limit.reset_at is None
        if not dormant_window and _utc_naive(limit.reset_at) != expected_reset_at:
            raise HTTPException(status_code=409, detail="The selected limit window has reset; create a new order")
        if limit.limit_window != LimitWindow.LIFETIME and expected_reset_at <= now:
            raise HTTPException(status_code=409, detail="The selected limit window has reset; create a new order")
        limit_update = update(ApiKeyLimit).where(ApiKeyLimit.id == limit.id).where(ApiKeyLimit.api_key_id == api_key.id)
        limit_update = (
            limit_update.where(ApiKeyLimit.reset_at.is_(None))
            if dormant_window
            else limit_update.where(ApiKeyLimit.reset_at == expected_reset_at)
        )
        result = await session.execute(
            limit_update.where(ApiKeyLimit.max_value <= MAX_PURCHASE_VALUE[limit_type] - purchased_value)
            .values(
                max_value=ApiKeyLimit.max_value + purchased_value,
                reset_at=func.coalesce(ApiKeyLimit.reset_at, expected_reset_at),
            )
            .returning(ApiKeyLimit.max_value, ApiKeyLimit.current_value, ApiKeyLimit.reset_at)
        )
        updated = result.first()
        if updated is None:
            await session.rollback()
            raise HTTPException(status_code=409, detail="The selected limit changed; retry the purchase")

        if mode_was_enabled:
            # Quota Shop Mode is a one-time choice. Atomically claim and turn
            # it off in the same transaction as the successful fulfillment.
            # A racing second order cannot consume another option.
            claimed = (
                await session.execute(
                    update(ApiKey)
                    .where(ApiKey.id == api_key.id)
                    .where(ApiKey.quota_shop_enabled.is_(True))
                    .values(quota_shop_enabled=False, quota_shop_max_windows=1)
                    .returning(ApiKey.id)
                )
            ).scalar_one_or_none()
            if claimed is None:
                await session.rollback()
                raise HTTPException(status_code=409, detail="Quota Shop choice was already used")

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

        if mode_was_enabled:
            await get_api_key_cache().invalidate(hashlib.sha256(payload.api_key.encode("utf-8")).hexdigest())
            poller = get_cache_invalidation_poller()
            if poller is not None:
                await poller.bump(NAMESPACE_API_KEY)

        current = max(0, min(int(updated.current_value), int(updated.max_value)))
        return QuotaShopFulfillResponse(
            success=True,
            idempotent=False,
            order_ref=payload.order_ref,
            key_prefix=_shop_key_prefix(api_key.key_prefix),
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
