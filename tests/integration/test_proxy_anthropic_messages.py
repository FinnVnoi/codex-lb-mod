from __future__ import annotations

import base64
import json

import pytest

import app.modules.proxy.service as proxy_module

pytestmark = pytest.mark.integration


def _encode_jwt(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    return f"header.{body}.sig"


def _make_auth_json(account_id: str, email: str) -> dict:
    payload = {
        "email": email,
        "chatgpt_account_id": account_id,
        "https://api.openai.com/auth": {"chatgpt_plan_type": "plus"},
    }
    return {
        "tokens": {
            "idToken": _encode_jwt(payload),
            "accessToken": "access-token",
            "refreshToken": "refresh-token",
            "accountId": account_id,
        },
    }


async def _import_account(async_client, account_id: str = "acc_anthropic_messages") -> None:
    auth_json = _make_auth_json(account_id, f"{account_id}@example.com")
    files = {"auth_json": ("auth.json", json.dumps(auth_json), "application/json")}
    response = await async_client.post("/api/accounts/import", files=files)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_v1_anthropic_messages_hides_upstream_quota_headers_for_api_key(
    async_client,
    monkeypatch,
):
    import app.modules.proxy.api as proxy_api

    api_key = object()

    async def hidden(_api_key: object) -> bool:
        assert _api_key is api_key
        return True

    class Service:
        async def rate_limit_headers(self) -> dict[str, str]:
            raise AssertionError("hidden API-key clients must not read upstream quota headers")

    context = type("Context", (), {"service": Service()})()
    monkeypatch.setattr(proxy_api, "_hide_upstream_quota_for_api_key_clients", hidden)

    headers = await proxy_api._rate_limit_headers_for_request(context, api_key)

    assert headers == {}


@pytest.mark.asyncio
async def test_v1_anthropic_messages_non_stream(async_client, monkeypatch):
    await _import_account(async_client)
    observed = {}

    async def fake_stream(payload, headers, access_token, account_id, base_url=None, raise_for_status=False):
        del headers, access_token, account_id, base_url, raise_for_status
        observed["instructions"] = payload.instructions
        observed["input"] = payload.input
        observed["tools"] = payload.tools
        yield 'data: {"type":"response.output_text.delta","delta":"Hello"}\n\n'
        yield 'data: {"type":"response.output_text.delta","delta":"!"}\n\n'
        yield (
            'data: {"type":"response.completed","response":{"id":"resp_anthropic_1",'
            '"usage":{"input_tokens":3,"output_tokens":2,"total_tokens":5}}}\n\n'
        )

    monkeypatch.setattr(proxy_module, "core_stream_responses", fake_stream)

    response = await async_client.post(
        "/v1/messages",
        json={
            "model": "gpt-5.2",
            "system": "be brief",
            "max_tokens": 64,
            "messages": [{"role": "user", "content": "hi"}],
            "tools": [
                {
                    "name": "lookup",
                    "description": "Lookup something",
                    "input_schema": {"type": "object", "properties": {"q": {"type": "string"}}},
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "id": "resp_anthropic_1",
        "type": "message",
        "role": "assistant",
        "model": "gpt-5.2",
        "content": [{"type": "text", "text": "Hello!"}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 3, "output_tokens": 2},
    }
    assert observed["instructions"] == "be brief"
    assert observed["input"] == [{"role": "user", "content": [{"type": "input_text", "text": "hi"}]}]
    assert observed["tools"] == [
        {
            "type": "function",
            "name": "lookup",
            "description": "Lookup something",
            "parameters": {"type": "object", "properties": {"q": {"type": "string"}}},
        }
    ]


@pytest.mark.asyncio
async def test_v1_anthropic_messages_ignores_stop_sequences(async_client, monkeypatch):
    await _import_account(async_client, "acc_anthropic_stop_sequences")
    observed = {}

    async def fake_stream(payload, headers, access_token, account_id, base_url=None, raise_for_status=False):
        del headers, access_token, account_id, base_url, raise_for_status
        observed["payload"] = payload.model_dump(mode="json", exclude_none=True)
        yield 'data: {"type":"response.output_text.delta","delta":"ok"}\n\n'
        yield (
            'data: {"type":"response.completed","response":{"id":"resp_anthropic_stop",'
            '"usage":{"input_tokens":1,"output_tokens":1,"total_tokens":2}}}\n\n'
        )

    monkeypatch.setattr(proxy_module, "core_stream_responses", fake_stream)

    response = await async_client.post(
        "/v1/messages",
        json={
            "model": "gpt-5.2",
            "max_tokens": 64,
            "stop_sequences": ["END"],
            "messages": [{"role": "user", "content": "hi"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["content"] == [{"type": "text", "text": "ok"}]
    assert "stop" not in observed["payload"]


@pytest.mark.asyncio
async def test_v1_anthropic_messages_stream(async_client, monkeypatch):
    await _import_account(async_client, "acc_anthropic_stream")

    async def fake_stream(payload, headers, access_token, account_id, base_url=None, raise_for_status=False):
        del payload, headers, access_token, account_id, base_url, raise_for_status
        yield 'data: {"type":"response.output_text.delta","delta":"Hi"}\n\n'
        yield (
            'data: {"type":"response.completed","response":{"id":"resp_anthropic_stream",'
            '"usage":{"input_tokens":4,"output_tokens":1,"total_tokens":5}}}\n\n'
        )

    monkeypatch.setattr(proxy_module, "core_stream_responses", fake_stream)

    async with async_client.stream(
        "POST",
        "/v1/messages",
        json={"model": "gpt-5.2", "max_tokens": 64, "stream": True, "messages": [{"role": "user", "content": "hi"}]},
    ) as response:
        assert response.status_code == 200
        text = "\n".join([line async for line in response.aiter_lines() if line])

    assert "event: message_start" in text
    assert "event: content_block_start" in text
    assert "event: content_block_delta" in text
    assert '"text":"Hi"' in text
    assert "event: message_delta" in text
    assert '"output_tokens":1' in text
    assert "event: message_stop" in text


@pytest.mark.asyncio
async def test_v1_anthropic_messages_tool_use_non_stream(async_client, monkeypatch):
    await _import_account(async_client, "acc_anthropic_tool")

    async def fake_stream(payload, headers, access_token, account_id, base_url=None, raise_for_status=False):
        del payload, headers, access_token, account_id, base_url, raise_for_status
        yield (
            'data: {"type":"response.output_item.done","output_index":0,"item":{"id":"fc_1",'
            '"type":"function_call","call_id":"toolu_1","name":"lookup","arguments":"{\\"q\\":\\"x\\"}"}}\n\n'
        )
        yield (
            'data: {"type":"response.completed","response":{"id":"resp_tool",'
            '"usage":{"input_tokens":5,"output_tokens":3,"total_tokens":8}}}\n\n'
        )

    monkeypatch.setattr(proxy_module, "core_stream_responses", fake_stream)

    response = await async_client.post(
        "/v1/messages",
        json={
            "model": "gpt-5.2",
            "max_tokens": 64,
            "messages": [{"role": "user", "content": "use tool"}],
            "tools": [{"name": "lookup", "input_schema": {"type": "object"}}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stop_reason"] == "tool_use"
    assert body["content"] == [{"type": "tool_use", "id": "toolu_1", "name": "lookup", "input": {"q": "x"}}]
