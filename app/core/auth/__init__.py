from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

DEFAULT_EMAIL = "unknown@example.com"
DEFAULT_PLAN = "unknown"


class WorkspaceClaim(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str | None = None
    workspace_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("workspace_id", "workspaceId"),
    )
    organization_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("organization_id", "organizationId", "org_id", "orgId"),
    )
    selected: bool | None = None
    active: bool | None = None
    current: bool | None = None
    default: bool | None = None
    is_default: bool | None = Field(default=None, validation_alias=AliasChoices("is_default", "isDefault"))

    def resolved_id(self) -> str | None:
        return self.workspace_id or self.organization_id or self.id

    def is_preferred(self) -> bool:
        return any(flag is True for flag in (self.selected, self.active, self.current, self.default, self.is_default))


class AuthTokens(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id_token: str = Field(alias="idToken")
    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    account_id: str | None = Field(default=None, alias="accountId")
    workspace_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "workspaceId",
            "workspace_id",
            "chatgptWorkspaceId",
            "chatgpt_workspace_id",
            "organizationId",
            "organization_id",
            "orgId",
            "org_id",
        ),
    )


class AuthFile(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    tokens: AuthTokens
    last_refresh_at: datetime | None = Field(default=None, alias="lastRefreshAt")
    workspace_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "workspaceId",
            "workspace_id",
            "chatgptWorkspaceId",
            "chatgpt_workspace_id",
            "organizationId",
            "organization_id",
            "orgId",
            "org_id",
        ),
    )


class OpenAIAuthClaims(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    chatgpt_account_id: str | None = None
    chatgpt_plan_type: str | None = None
    workspace_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("workspace_id", "workspaceId", "organization_id", "organizationId"),
    )
    organizations: list[WorkspaceClaim] | None = None


class IdTokenClaims(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    email: str | None = None
    chatgpt_account_id: str | None = None
    chatgpt_plan_type: str | None = None
    workspace_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("workspace_id", "workspaceId", "organization_id", "organizationId"),
    )
    organizations: list[WorkspaceClaim] | None = None
    exp: int | float | str | None = None
    auth: OpenAIAuthClaims | None = Field(
        default=None,
        alias="https://api.openai.com/auth",
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
    plan_type = auth_claims.chatgpt_plan_type or claims.chatgpt_plan_type
    return AccountClaims(
        account_id=resolve_chatgpt_account_id(auth=auth, claims=claims),
        email=claims.email,
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


def resolve_chatgpt_account_id(*, auth: AuthFile | None = None, claims: IdTokenClaims | None = None) -> str | None:
    token_claims = claims
    if token_claims is None and auth is not None:
        token_claims = extract_id_token_claims(auth.tokens.id_token)

    auth_claims = token_claims.auth if token_claims and token_claims.auth else OpenAIAuthClaims()

    for candidate in (
        auth.tokens.workspace_id if auth is not None else None,
        auth.workspace_id if auth is not None else None,
        auth_claims.workspace_id,
        _workspace_id_from_organizations(auth_claims.organizations),
        token_claims.workspace_id if token_claims is not None else None,
        _workspace_id_from_organizations(token_claims.organizations if token_claims is not None else None),
        auth.tokens.account_id if auth is not None else None,
        auth_claims.chatgpt_account_id,
        token_claims.chatgpt_account_id if token_claims is not None else None,
    ):
        normalized = _normalize_identifier(candidate)
        if normalized:
            return normalized
    return None


def _workspace_id_from_organizations(organizations: list[WorkspaceClaim] | None) -> str | None:
    if not organizations:
        return None
    preferred = [org for org in organizations if org.is_preferred() and org.resolved_id()]
    if preferred:
        return preferred[0].resolved_id()
    for organization in organizations:
        resolved = organization.resolved_id()
        if resolved:
            return resolved
    return None


def _normalize_identifier(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
