from __future__ import annotations

import base64
import json
import os
import stat

import pytest
from cryptography.fernet import InvalidToken
from pydantic import ValidationError

from app.core.auth import claims_from_auth, extract_id_token_claims, parse_auth_json
from app.core.crypto import TokenEncryptor, get_or_create_key

pytestmark = pytest.mark.unit


def _encode_jwt(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    return f"header.{body}.sig"


def test_extract_id_token_claims_valid_payload():
    payload = {"email": "user@example.com", "chatgpt_account_id": "acc_123"}
    token = _encode_jwt(payload)
    claims = extract_id_token_claims(token)
    assert claims.email == "user@example.com"
    assert claims.chatgpt_account_id == "acc_123"


def test_claims_from_auth_prefers_token_account_id():
    payload = {
        "email": "user@example.com",
        "chatgpt_account_id": "acc_payload",
        "https://api.openai.com/auth": {"chatgpt_plan_type": "plus"},
    }
    token = _encode_jwt(payload)
    auth_json = {
        "tokens": {
            "idToken": token,
            "accessToken": "access",
            "refreshToken": "refresh",
            "accountId": "acc_explicit",
        },
        "lastRefreshAt": "2024-01-01T00:00:00Z",
    }
    auth = parse_auth_json(json.dumps(auth_json).encode("utf-8"))
    claims = claims_from_auth(auth)
    assert claims.account_id == "acc_explicit"
    assert claims.email == "user@example.com"
    assert claims.plan_type == "plus"


def test_parse_auth_json_accepts_latest_codex_export_format():
    auth_json = {
        "auth_mode": "chatgpt",
        "OPENAI_API_KEY": None,
        "tokens": {
            "id_token": "id",
            "access_token": "access",
            "refresh_token": "refresh",
            "account_id": "acc_latest",
        },
        "last_refresh": "2024-01-02T03:04:05Z",
    }

    auth = parse_auth_json(json.dumps(auth_json).encode("utf-8"))

    assert auth.tokens.id_token == "id"
    assert auth.tokens.access_token == "access"
    assert auth.tokens.refresh_token == "refresh"
    assert auth.tokens.account_id == "acc_latest"
    assert auth.last_refresh_at is not None
    assert auth.last_refresh_at.isoformat() == "2024-01-02T03:04:05+00:00"


def test_parse_auth_json_accepts_cliproxyapi_codex_flat_format():
    payload = {
        "https://api.openai.com/auth": {"chatgpt_plan_type": "team"},
    }
    token = _encode_jwt(payload)
    auth_json = {
        "type": "codex",
        "id_token": token,
        "access_token": "access-cpa",
        "refresh_token": "refresh-cpa",
        "account_id": "acc_cpa",
        "email": "cpa@example.com",
        "expired": "2024-01-02T04:04:05Z",
        "last_refresh": "2024-01-02T03:04:05Z",
    }

    auth = parse_auth_json(json.dumps(auth_json).encode("utf-8"))

    assert auth.tokens.id_token == token
    assert auth.tokens.access_token == "access-cpa"
    assert auth.tokens.refresh_token == "refresh-cpa"
    assert auth.tokens.account_id == "acc_cpa"
    assert auth.email == "cpa@example.com"
    assert auth.last_refresh_at is not None
    assert auth.last_refresh_at.isoformat() == "2024-01-02T03:04:05+00:00"

    claims = claims_from_auth(auth)
    assert claims.account_id == "acc_cpa"
    assert claims.email == "cpa@example.com"
    assert claims.plan_type == "team"


def test_parse_auth_json_accepts_cliproxyapi_access_token_only_export():
    payload = {
        "https://api.openai.com/auth": {
            "chatgpt_account_id": "acc_cpa_access",
            "chatgpt_plan_type": "plus",
        },
        "https://api.openai.com/profile": {"email": "profile@example.com"},
    }
    token = _encode_jwt(payload)
    auth_json = {
        "type": "codex",
        "access_token": token,
        "account_id": "acc_cpa_access",
        "email": "fallback@example.com",
    }

    auth = parse_auth_json(json.dumps(auth_json).encode("utf-8"))

    assert auth.tokens.id_token == token
    assert auth.tokens.access_token == token
    assert auth.tokens.refresh_token == ""

    claims = claims_from_auth(auth)
    assert claims.account_id == "acc_cpa_access"
    assert claims.email == "profile@example.com"
    assert claims.plan_type == "plus"


def test_parse_auth_json_rejects_non_codex_flat_token_payload():
    auth_json = {
        "type": "xai",
        "id_token": "id",
        "access_token": "access",
        "refresh_token": "refresh",
        "account_id": "acc_xai",
    }

    with pytest.raises(ValidationError):
        parse_auth_json(json.dumps(auth_json).encode("utf-8"))


def test_claims_from_auth_preserves_prolite_plan_type():
    payload = {
        "email": "user@example.com",
        "chatgpt_account_id": "acc_payload",
        "https://api.openai.com/auth": {"chatgpt_plan_type": "prolite"},
    }
    token = _encode_jwt(payload)
    auth_json = {
        "tokens": {
            "idToken": token,
            "accessToken": "access",
            "refreshToken": "refresh",
            "accountId": "acc_explicit",
        },
    }
    auth = parse_auth_json(json.dumps(auth_json).encode("utf-8"))
    claims = claims_from_auth(auth)
    assert claims.plan_type == "prolite"


def test_key_file_permissions_and_reuse(temp_key_file):
    first = get_or_create_key()
    second = get_or_create_key()
    assert first == second
    if os.name == "nt":
        pytest.skip("POSIX chmod semantics are not enforced on Windows")
    mode = stat.S_IMODE(temp_key_file.stat().st_mode)
    assert mode == 0o600


def test_token_encryptor_round_trip():
    encryptor = TokenEncryptor()
    value = "secret-token"
    encrypted = encryptor.encrypt(value)
    assert encryptor.decrypt(encrypted) == value


def test_token_encryptor_invalid_token_raises():
    encryptor = TokenEncryptor()
    with pytest.raises(InvalidToken):
        encryptor.decrypt(b"not-a-token")
