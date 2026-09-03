from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import ProxyRateLimitError
from app.core.handlers import add_exception_handlers

MESSAGE = "Đã đạt đến giới hạn. Vui lòng nạp thêm quota."


def _app() -> FastAPI:
    app = FastAPI()
    add_exception_handlers(app)

    @app.post("/backend-api/codex/responses")
    async def responses() -> None:
        raise ProxyRateLimitError(MESSAGE)

    @app.post("/v1/responses")
    async def v1_responses() -> None:
        raise ProxyRateLimitError(MESSAGE)

    @app.post("/v1/responses/compact")
    async def compact() -> None:
        raise ProxyRateLimitError(MESSAGE)

    return app


def _sse_payload(response_text: str) -> dict[str, Any]:
    data_line = next(line for line in response_text.splitlines() if line.startswith("data: "))
    return json.loads(data_line.removeprefix("data: "))


def test_codex_user_agent_receives_localized_rate_limit_as_terminal_sse() -> None:
    with TestClient(_app()) as client:
        response = client.post(
            "/backend-api/codex/responses",
            headers={"User-Agent": "codex_cli_rs/0.145.0"},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    payload = _sse_payload(response.text)
    assert payload["type"] == "response.failed"
    assert payload["response"]["status"] == "failed"
    assert payload["response"]["error"] == {
        "message": MESSAGE,
        "type": "rate_limit_error",
        "code": "rate_limit_exceeded",
    }


def test_codex_user_agent_matching_is_case_insensitive_on_v1_responses() -> None:
    with TestClient(_app()) as client:
        response = client.post("/v1/responses", headers={"User-Agent": "My-CoDeX-Client"})

    assert response.status_code == 200
    assert _sse_payload(response.text)["type"] == "response.failed"


def test_non_codex_user_agent_keeps_standard_http_429_json() -> None:
    with TestClient(_app()) as client:
        response = client.post(
            "/backend-api/codex/responses",
            headers={"User-Agent": "openai-python/2.0"},
        )

    assert response.status_code == 429
    assert response.json() == {
        "error": {
            "message": MESSAGE,
            "type": "rate_limit_error",
            "code": "rate_limit_exceeded",
        }
    }


def test_codex_user_agent_on_non_responses_route_keeps_http_429() -> None:
    with TestClient(_app()) as client:
        response = client.post(
            "/v1/responses/compact",
            headers={"User-Agent": "codex_cli_rs/0.145.0"},
        )

    assert response.status_code == 429
