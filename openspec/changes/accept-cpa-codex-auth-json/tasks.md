## 1. Parser Compatibility

- [x] 1.1 Detect flat CLIProxyAPI Codex auth JSON with top-level token fields.
- [x] 1.2 Normalize flat Codex token fields into the existing `tokens` object before validation.
- [x] 1.3 Preserve existing Codex CLI auth JSON parsing behavior and avoid normalizing flat payloads without `type: "codex"`.
- [x] 1.4 Fall back to top-level `email` when the ID token does not expose an email claim.

## 2. Tests

- [x] 2.1 Add unit coverage for CLIProxyAPI flat Codex auth JSON and non-Codex flat token rejection.
- [x] 2.2 Run the focused auth parser tests.
- [x] 2.3 `openspec validate --specs` unavailable: no `openspec` executable is installed in this environment.
