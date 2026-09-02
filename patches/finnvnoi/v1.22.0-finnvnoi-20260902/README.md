# FinnVnoi Codex-LB patches — v1.22.0 / 2026-09-02

This bundle captures the FinnVnoi production source customizations through 2026-09-02.
It is based on upstream Codex-LB **v1.22.0** at `4c0dbc9ceb2b5d70204ea7603cf1b4bef83db234`.

## Canonical snapshot

- Git branch:   `local/v1.22.0-finnvnoi-20260902`
- Source snapshot commit (before this bundle metadata):   `c61fddf08e9854820771ee8037954aa277713a30`
- Patch SHA-256:   `e088334d69681d552b3180d0588051daec95726af192afed1ce155cfded9d0bd`

The branch is the canonical source snapshot and preserves Git history. The patch is the
portable recovery artifact for applying the same source tree to a clean v1.22.0 checkout.
Runtime databases, environment files, credentials, static build output, backups, and logs
are intentionally excluded.

## Included customization groups

1. API-key compatibility and controls
   - CPA Codex auth JSON import and expiring      `sk-amin` keys
   - bulk/lifetime usage compatibility, hourly and lifetime limits
   - dynamic quota shop, independent quota mode/options, expiry auto-extension
   - logical downstream request accounting and activity API
2. Routing and failover
   - global/provider/account routing policies and dashboard controls
   - provider cycling, account/provider fallback, stream startup probing
   - sticky/affinity-aware routing and retry-chain suppression
   - configurable attempts and bridge retirement after explicit quota/rate-limit events
3. Model Sources
   - stream usage parsing including EOF handling and missing-usage estimation
   - sticky settings, usage accounting, provider status/error visibility
   - consecutive-failure auto-pause with configurable threshold and resume support
4. Protocol compatibility
   - Anthropic Messages support for Claude Code
   - OpenAI/Responses request normalization and resilient compact/replay handling
   - GPT-5.6 pricing compatibility and WebSocket/HTTP bridge diagnostics
5. Dashboard and localization
   - API routing master controls, Traffic routing & failover settings
   - API-key quota controls and Model Source settings/status
   - English and Vietnamese labels plus regression tests
6. Database migrations and recovery helpers
   - FinnVnoi migration chain through      `20260902_000000_add_model_source_auto_pause`
   - logical-request backfill helper and focused OpenSpec notes

## Apply

Start from a clean upstream v1.22.0 checkout:

```bash
git checkout v1.22.0
./patches/finnvnoi/v1.22.0-finnvnoi-20260902/apply.sh --check
./patches/finnvnoi/v1.22.0-finnvnoi-20260902/apply.sh
```

The script changes source only. Review configuration, back up the database, run migrations,
build the frontend, and run tests before restarting a deployed service.

## Verification used when publishing

- exact tree comparison after applying the patch to a clean v1.22.0 worktree
-   `git diff --check`
- credential-pattern scan over all changed/untracked source paths
- focused backend/frontend tests were invoked; see repository commit notes for any baseline or
  environment failures rather than treating a partially failing broad suite as a clean pass
