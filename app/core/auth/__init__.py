from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

DEFAULT_EMAIL = "unknown@example.com"
DEFAULT_PLAN = "unknown"


class AuthTokens(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id_token: str = Field(alias="idToken")
    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    account_id: str | None = Field(default=None, alias="accountId")


class AuthFile(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    tokens: AuthTokens
    last_refresh_at: datetime | None = Field(
        default=None,
        alias="lastRefreshAt",
        validation_alias=AliasChoices("lastRefreshAt", "last_refresh"),
        serialization_alias="lastRefreshAt",
    )
    email: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _accept_flat_codex_tokens(cls, value: object) -> object:
        """Accept CLIProxyAPI's flat Codex auth JSON shape.

        CLIProxyAPI stores Codex credentials as top-level ``id_token``,
        ``access_token``, ``refresh_token``, and ``account_id`` fields rather
        than under Codex CLI's ``tokens`` object.  Normalize that shape before
        Pydantic validates the canonical model.
        """
        if not isinstance(value, dict) or "tokens" in value:
            return value

        provider = str(value.get("type") or "").strip().lower()
        if provider != "codex":
            return value

        id_token = value.get("id_token") or value.get("idToken")
        access_token = value.get("access_token") or value.get("accessToken")
        refresh_token = value.get("refresh_token") or value.get("refreshToken")
        account_id = value.get("account_id") or value.get("accountId")
        if id_token is None and access_token:
            # CPA bundle exports can contain only the long-lived ChatGPT access
            # token. It is still a JWT with the ChatGPT account/profile claims
            # codex-lb needs for identity, so use it as the claim-bearing token.
            id_token = access_token
        if refresh_token is None and access_token:
            # Access-token-only imports are usable until the token expires, but
            # cannot be refreshed. Store an empty marker instead of rejecting
            # the account so operators can import CPA bundles directly.
            refresh_token = ""
        if not any((id_token, access_token, refresh_token, account_id)):
            return value

        normalized = dict(value)
        normalized["tokens"] = {
            "id_token": id_token,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "account_id": account_id,
        }
        return normalized



class OpenAIAuthClaims(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chatgpt_account_id: str | None = None
    chatgpt_plan_type: str | None = None


class OpenAIProfileClaims(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str | None = None


class IdTokenClaims(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    email: str | None = None
    chatgpt_account_id: str | None = None
    chatgpt_plan_type: str | None = None
    exp: int | float | str | None = None
    auth: OpenAIAuthClaims | None = Field(
        default=None,
        alias="https://api.openai.com/auth",
    )
    profile: OpenAIProfileClaims | None = Field(
        default=None,
        alias="https://api.openai.com/profile",
    )


@dataclass
class AccountClaims:
    account_id: str | None
    email: str | None
    plan_type: str | None


def parse_auth_json(raw: bytes) -> AuthFile:
    data = json.loads(raw)
    model = AuthFile.model_validate(data)
    return model


def extract_id_token_claims(id_token: str) -> IdTokenClaims:
    try:
        parts = id_token.split(".")
        if len(parts) < 2:
            return IdTokenClaims()
        payload = parts[1]
        padding = "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload + padding)
        data = json.loads(decoded)
        if not isinstance(data, dict):
            return IdTokenClaims()
        return IdTokenClaims.model_validate(data)
    except Exception:
        return IdTokenClaims()


def claims_from_auth(auth: AuthFile) -> AccountClaims:
    claims = extract_id_token_claims(auth.tokens.id_token)
    auth_claims = claims.auth or OpenAIAuthClaims()
    profile_claims = claims.profile or OpenAIProfileClaims()
    plan_type = auth_claims.chatgpt_plan_type or claims.chatgpt_plan_type
    return AccountClaims(
        account_id=auth.tokens.account_id or auth_claims.chatgpt_account_id or claims.chatgpt_account_id,
        email=claims.email or profile_claims.email or auth.email,
        plan_type=plan_type,
    )


def generate_unique_account_id(account_id: str | None, email: str | None) -> str:
    if account_id and email and email != DEFAULT_EMAIL:
        email_hash = hashlib.sha256(email.encode()).hexdigest()[:8]
        return f"{account_id}_{email_hash}"
    if account_id:
        return account_id
    return fallback_account_id(email)


def fallback_account_id(email: str | None) -> str:
    """Generate a fallback account ID when no OpenAI account ID is available."""
    if email and email != DEFAULT_EMAIL:
        digest = hashlib.sha256(email.encode()).hexdigest()[:12]
        return f"email_{digest}"
    return f"local_{uuid4().hex[:12]}"
