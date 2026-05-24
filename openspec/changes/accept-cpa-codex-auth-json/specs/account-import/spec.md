## ADDED Requirements

### Requirement: Import CLIProxyAPI flat Codex auth JSON

The account import parser MUST accept CLIProxyAPI Codex auth JSON files that identify themselves as Codex credentials and store OAuth token fields at the top level rather than under a `tokens` object. At minimum, the parser MUST map top-level `id_token`, `access_token`, `refresh_token`, and `account_id` fields into the same internal token model used for Codex CLI auth JSON imports.

The parser MUST continue to accept existing Codex CLI auth JSON formats. If the ID token does not include an email claim and the CLIProxyAPI JSON provides a top-level `email`, the import flow MUST use that email as the account email fallback. The parser MUST NOT apply the flat CLIProxyAPI Codex-token normalization unless the flat payload identifies itself with `type: "codex"`.

#### Scenario: CLIProxyAPI flat JSON import

- **WHEN** a user uploads a Codex auth JSON file containing top-level `type: "codex"`, `id_token`, `access_token`, `refresh_token`, `account_id`, `email`, and `last_refresh`
- **THEN** the import parser accepts the file
- **AND** the imported account uses the mapped token values
- **AND** the account email falls back to the top-level `email` if the ID token has no email claim

#### Scenario: Existing Codex CLI import still works

- **WHEN** a user uploads a Codex CLI auth JSON file with token fields under `tokens`
- **THEN** the import parser accepts the file using the existing token mapping

#### Scenario: Non-Codex flat token payload is not normalized

- **WHEN** a user uploads a flat token JSON file with top-level token fields and no `type: "codex"` marker
- **THEN** the Codex account import parser rejects it instead of treating it as a Codex account
