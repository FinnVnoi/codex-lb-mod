# FinnVnoi Codex-LB patches — v1.22.0 / 2026-09-03

This bundle captures FinnVnoi production source customizations through 2026-09-03.
It is based on upstream Codex-LB **v1.22.0** at `4c0dbc9ceb2b5d70204ea7603cf1b4bef83db234`.

## Canonical snapshot

- Git branch: `local/v1.22.0-finnvnoi-20260903`
- Source snapshot commit: `9e3035b4b8305f0bb4ec3162540393b0641b4374`
- Source tree: `fe43ad85dbbfcf4c96ac28dea58182d78f116088`
- Patch SHA-256: `1de6166306a246a7c9ab8a12258f9f1667b1585accba92716ed573df3a1dd8b5`

Runtime databases, environment files, credentials, build output, backups, and logs are excluded.

## Changes since the 2026-09-02 bundle

- Codex User-Agent quota errors preserve the localized message in terminal SSE instead of degrading to a generic retry-limit error.
- Usage activity adds lifetime per-model aggregates independent of retained request-row pagination.
- Rolling API-key limits remain dormant at zero usage and start their countdown atomically on first positive usage.
- Ordinary admin edits, including changing max limit, preserve usage and the current countdown; explicit Reset usage clears both usage and the rolling countdown.
- Nullable reset timestamps are supported across API responses, proxy usage compatibility, quota shop, warmup, frontend schemas, and reservation CAS logic.

## Apply to v1.22.0

```bash
git checkout v1.22.0
./patches/finnvnoi/v1.22.0-finnvnoi-20260903/apply.sh --check
./patches/finnvnoi/v1.22.0-finnvnoi-20260903/apply.sh
```

For v1.24.0 use the compatibility report/port branch published separately; this exact overlay intentionally targets v1.22.0.
