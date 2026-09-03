from types import SimpleNamespace

from fastapi import Response
from starlette.requests import Request

from app.modules.proxy import api


def _request() -> Request:
    return Request({"type": "http", "method": "POST", "path": "/responses", "headers": []})


def _key(mode: str):
    return SimpleNamespace(id="key-tan", routing_mode=mode)


def test_balanced_alternates_once_per_inbound_request() -> None:
    api._SOURCE_ROUTE_CURSOR.clear()
    first = _request()
    assert api._route_to_provider_for_native_model(_key("balanced"), model="gpt-5.6-sol", request=first)
    assert api._route_to_provider_for_native_model(_key("balanced"), model="gpt-5.6-sol", request=first)
    second = _request()
    assert not api._route_to_provider_for_native_model(_key("balanced"), model="gpt-5.6-sol", request=second)


def test_explicit_modes_do_not_alternate() -> None:
    assert api._route_to_provider_for_native_model(_key("provider_first"), model="gpt-5.6-sol")
    assert not api._route_to_provider_for_native_model(_key("account_first"), model="gpt-5.6-sol")


def test_account_capacity_error_allows_provider_fallback() -> None:
    response = Response(
        content=b'{"error":{"code":"no_accounts","message":"No available accounts"}}',
        status_code=503,
    )
    assert api._account_response_allows_provider_fallback(response)


def test_client_payload_error_does_not_fallback() -> None:
    response = Response(
        content=b'{"error":{"code":"invalid_request_error","message":"Item with id rs_x not found"}}',
        status_code=404,
    )
    assert not api._account_response_allows_provider_fallback(response)
