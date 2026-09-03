## Why

CLIProxyAPI persists Codex OAuth credentials as flat auth JSON files with top-level `type`, `id_token`, `access_token`, `refresh_token`, `account_id`, `email`, `expired`, and `last_refresh` fields. `codex-lb` account import currently accepts Codex CLI-style JSON where token fields live under `tokens`, so operators cannot directly reuse CLIProxyAPI Codex auth exports.

## What Changes

- Normalize CLIProxyAPI's flat Codex token fields into `codex-lb`'s existing `AuthFile.tokens` model during import parsing.
- Preserve the existing Codex CLI export formats unchanged.
- Use CLIProxyAPI's top-level `email` as a fallback when the ID token does not contain an email claim.

## Capabilities

### Added Capabilities

- `account-import`: the account import API accepts CLIProxyAPI flat Codex auth JSON in addition to existing Codex CLI JSON shapes.

## Impact

- **Code**: `app/core/auth/__init__.py`
- **Tests**: `tests/unit/test_auth.py`
- **API surface**: `POST /api/accounts/import` accepts an additional compatible JSON shape; no endpoint or response contract changes.
- **Operational**: no migration or configuration required.
