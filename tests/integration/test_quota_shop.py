from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.utils.time import utcnow
from app.db.models import ApiKeyLimit, ApiKeyQuotaPurchase
from app.db.session import SessionLocal
from app.modules.api_keys.repository import ApiKeysRepository
from app.modules.api_keys.service import ApiKeyCreateData, ApiKeysService, LimitRuleInput

pytestmark = pytest.mark.integration


async def _create_key() -> tuple[str, str]:
    async with SessionLocal() as session:
        created = await ApiKeysService(ApiKeysRepository(session)).create_key(
            ApiKeyCreateData(
                name="quota-shop-test",
                allowed_models=None,
                limits=[
                    LimitRuleInput(
                        limit_type="total_tokens",
                        limit_window="lifetime",
                        max_value=10_000_000,
                    ),
                    LimitRuleInput(
                        limit_type="total_tokens",
                        limit_window="5h",
                        max_value=4_000_000,
                    ),
                    LimitRuleInput(
                        limit_type="cost_usd",
                        limit_window="lifetime",
                        max_value=3_000_000,
                    ),
                    LimitRuleInput(
                        limit_type="cost_usd",
                        limit_window="weekly",
                        max_value=5_000_000,
                        model_filter="gpt-5.4",
                    ),
                    LimitRuleInput(
                        limit_type="input_tokens",
                        limit_window="daily",
                        max_value=100_000,
                    ),
                ],
            )
        )
    return created.id, created.key


@pytest.mark.asyncio
async def test_catalog_returns_all_supported_type_window_rules(async_client):
    _, raw_key = await _create_key()
    response = await async_client.get(
        "/v1/quota-shop/catalog",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert response.status_code == 200
    body = response.json()
    identities = {(rule["limit_type"], rule["limit_window"], rule["model_filter"]) for rule in body["rules"]}
    assert identities == {
        ("total_tokens", "lifetime", None),
        ("total_tokens", "5h", None),
        ("cost_usd", "lifetime", None),
        ("cost_usd", "weekly", "gpt-5.4"),
    }
    assert all(rule["unit_size"] == 1_000_000 for rule in body["rules"])
    assert all("price_vnd_per_unit" not in rule for rule in body["rules"])


@pytest.mark.asyncio
async def test_fulfill_increments_matching_lifetime_rule_and_is_idempotent(async_client, monkeypatch):
    key_id, raw_key = await _create_key()
    monkeypatch.setenv("CODEX_LB_QUOTA_SHOP_SECRET", "test-secret")

    async with SessionLocal() as session:
        result = await session.execute(
            select(ApiKeyLimit).where(
                ApiKeyLimit.api_key_id == key_id,
                ApiKeyLimit.limit_type == "total_tokens",
                ApiKeyLimit.limit_window == "lifetime",
            )
        )
        limit = result.scalar_one()
        original_max = limit.max_value

    payload = {
        "order_ref": "SHOP:1001",
        "api_key": raw_key,
        "limit_id": limit.id,
        "purchased_value": 2_000_000,
        "amount_vnd": 4000,
        "limit_type": "total_tokens",
        "limit_window": "lifetime",
        "model_filter": None,
        "target_reset_at": limit.reset_at.isoformat() + "Z",
    }
    first = await async_client.post(
        "/v1/quota-shop/fulfill",
        headers={"X-Quota-Shop-Secret": "test-secret"},
        json=payload,
    )
    assert first.status_code == 200, first.text
    assert first.json()["idempotent"] is False
    assert first.json()["new_max_value"] == original_max + 2_000_000

    second = await async_client.post(
        "/v1/quota-shop/fulfill",
        headers={"X-Quota-Shop-Secret": "test-secret"},
        json=payload,
    )
    assert second.status_code == 200, second.text
    assert second.json()["idempotent"] is True
    assert second.json()["new_max_value"] == original_max + 2_000_000

    async with SessionLocal() as session:
        refreshed = await session.get(ApiKeyLimit, limit.id)
        purchases = (
            (await session.execute(select(ApiKeyQuotaPurchase).where(ApiKeyQuotaPurchase.order_ref == "SHOP:1001")))
            .scalars()
            .all()
        )
        assert refreshed is not None
        assert refreshed.max_value == original_max + 2_000_000
        assert len(purchases) == 1


@pytest.mark.asyncio
async def test_periodic_purchase_is_removed_at_selected_rule_reset(async_client, monkeypatch):
    key_id, raw_key = await _create_key()
    monkeypatch.setenv("CODEX_LB_QUOTA_SHOP_SECRET", "test-secret")
    async with SessionLocal() as session:
        result = await session.execute(
            select(ApiKeyLimit).where(
                ApiKeyLimit.api_key_id == key_id,
                ApiKeyLimit.limit_type == "cost_usd",
                ApiKeyLimit.limit_window == "weekly",
            )
        )
        limit = result.scalar_one()
        original_max = limit.max_value
        old_reset = utcnow() + timedelta(seconds=30)
        limit.reset_at = old_reset
        await session.commit()

    payload = {
        "order_ref": "SHOP:weekly-reset",
        "api_key": raw_key,
        "limit_id": limit.id,
        "purchased_value": 2_000_000,
        "amount_vnd": 3000,
        "limit_type": "cost_usd",
        "limit_window": "weekly",
        "model_filter": "gpt-5.4",
        "target_reset_at": old_reset.isoformat() + "Z",
    }
    response = await async_client.post(
        "/v1/quota-shop/fulfill",
        headers={"X-Quota-Shop-Secret": "test-secret"},
        json=payload,
    )
    assert response.status_code == 200, response.text
    assert response.json()["new_max_value"] == original_max + 2_000_000

    async with SessionLocal() as session:
        repo = ApiKeysRepository(session)
        changed = await repo.reset_limit(
            limit.id,
            expected_reset_at=old_reset,
            new_reset_at=old_reset + timedelta(days=7),
        )
        assert changed is True
        refreshed = await session.get(ApiKeyLimit, limit.id)
        assert refreshed is not None
        assert refreshed.max_value == original_max
        assert refreshed.current_value == 0


@pytest.mark.asyncio
async def test_periodic_order_snapshot_cannot_cross_reset_boundary(async_client, monkeypatch):
    key_id, raw_key = await _create_key()
    monkeypatch.setenv("CODEX_LB_QUOTA_SHOP_SECRET", "test-secret")
    async with SessionLocal() as session:
        result = await session.execute(
            select(ApiKeyLimit).where(
                ApiKeyLimit.api_key_id == key_id,
                ApiKeyLimit.limit_type == "total_tokens",
                ApiKeyLimit.limit_window == "5h",
            )
        )
        limit = result.scalar_one()
        original_max = limit.max_value
        order_reset = limit.reset_at
        limit.reset_at = order_reset + timedelta(hours=5)
        await session.commit()

    response = await async_client.post(
        "/v1/quota-shop/fulfill",
        headers={"X-Quota-Shop-Secret": "test-secret"},
        json={
            "order_ref": "SHOP:stale-5h",
            "api_key": raw_key,
            "limit_id": limit.id,
            "purchased_value": 1_000_000,
            "amount_vnd": 2000,
            "limit_type": "total_tokens",
            "limit_window": "5h",
            "model_filter": None,
            "target_reset_at": order_reset.isoformat() + "Z",
        },
    )
    assert response.status_code == 409, response.text
    assert "has reset" in response.json()["error"]["message"]

    async with SessionLocal() as session:
        refreshed = await session.get(ApiKeyLimit, limit.id)
        purchase = (
            await session.execute(select(ApiKeyQuotaPurchase).where(ApiKeyQuotaPurchase.order_ref == "SHOP:stale-5h"))
        ).scalar_one_or_none()
        assert refreshed is not None
        assert refreshed.max_value == original_max
        assert purchase is None


@pytest.mark.asyncio
async def test_expired_periodic_rule_cannot_be_fulfilled(async_client, monkeypatch):
    key_id, raw_key = await _create_key()
    monkeypatch.setenv("CODEX_LB_QUOTA_SHOP_SECRET", "test-secret")
    async with SessionLocal() as session:
        result = await session.execute(
            select(ApiKeyLimit).where(
                ApiKeyLimit.api_key_id == key_id,
                ApiKeyLimit.limit_type == "total_tokens",
                ApiKeyLimit.limit_window == "5h",
            )
        )
        limit = result.scalar_one()
        original_max = limit.max_value
        limit.reset_at = utcnow() - timedelta(seconds=1)
        await session.commit()

    response = await async_client.post(
        "/v1/quota-shop/fulfill",
        headers={"X-Quota-Shop-Secret": "test-secret"},
        json={
            "order_ref": "SHOP:expired-5h",
            "api_key": raw_key,
            "limit_id": limit.id,
            "purchased_value": 1_000_000,
            "amount_vnd": 2000,
            "limit_type": "total_tokens",
            "limit_window": "5h",
            "model_filter": None,
            "target_reset_at": limit.reset_at.isoformat() + "Z",
        },
    )
    assert response.status_code == 409, response.text
    assert "has reset" in response.json()["error"]["message"]

    async with SessionLocal() as session:
        refreshed = await session.get(ApiKeyLimit, limit.id)
        purchase = (
            await session.execute(select(ApiKeyQuotaPurchase).where(ApiKeyQuotaPurchase.order_ref == "SHOP:expired-5h"))
        ).scalar_one_or_none()
        assert refreshed is not None
        assert refreshed.max_value == original_max
        assert purchase is None


@pytest.mark.asyncio
async def test_purchase_accepts_exact_vnd_amount_and_enforces_secret(async_client, monkeypatch):
    key_id, raw_key = await _create_key()
    monkeypatch.setenv("CODEX_LB_QUOTA_SHOP_SECRET", "test-secret")
    async with SessionLocal() as session:
        result = await session.execute(
            select(ApiKeyLimit).where(
                ApiKeyLimit.api_key_id == key_id,
                ApiKeyLimit.limit_type == "cost_usd",
                ApiKeyLimit.limit_window == "lifetime",
            )
        )
        limit = result.scalar_one()

    payload = {
        "order_ref": "SHOP:1002",
        "api_key": raw_key,
        "limit_id": limit.id,
        "purchased_value": 333_333,
        "amount_vnd": 750,
        "limit_type": "cost_usd",
        "limit_window": "lifetime",
        "model_filter": None,
        "target_reset_at": limit.reset_at.isoformat() + "Z",
    }
    response = await async_client.post(
        "/v1/quota-shop/fulfill",
        headers={"X-Quota-Shop-Secret": "test-secret"},
        json=payload,
    )
    assert response.status_code == 200, response.text
    assert response.json()["amount_vnd"] == 750
    assert response.json()["purchased_value"] == 333_333

    payload["order_ref"] = "SHOP:1003"
    payload["amount_vnd"] = 123
    response = await async_client.post(
        "/v1/quota-shop/fulfill",
        headers={"X-Quota-Shop-Secret": "wrong"},
        json=payload,
    )
    assert response.status_code == 401
