# FinnVnoi local patch bundle for codex-lb v1.20.2-beta.1

Base upstream tag: `v1.20.2-beta.1` (`ea2abfa456f0`)
Generated from FinnVnoi mod branch: `local/v1.20.2-beta.1-finnvnoi-patches`
Source commit: `58064d9a43cc`

This bundle captures FinnVnoi's local codex-lb mods so they can be replayed after a fresh upstream checkout/update.

Included patch:

- `0001-finnvnoi-local-mods-v1.20.2-beta.1.patch` — full local diff from upstream `v1.20.2-beta.1` to the source commit above.

## Option A: use the pre-patched branch directly

```bash
git fetch origin local/v1.20.2-beta.1-finnvnoi-patches
git checkout -B finnvnoi-codex-lb origin/local/v1.20.2-beta.1-finnvnoi-patches
```

## Option B: apply the patch bundle onto a clean upstream checkout

```bash
git fetch --tags upstream
git fetch origin local/v1.20.2-beta.1-finnvnoi-patches
git checkout -B finnvnoi-reapply v1.20.2-beta.1
git restore --source origin/local/v1.20.2-beta.1-finnvnoi-patches -- patches/finnvnoi/v1.20.2-beta.1
patches/finnvnoi/v1.20.2-beta.1/apply.sh --check
patches/finnvnoi/v1.20.2-beta.1/apply.sh
```

If applying onto a newer upstream tag/branch, replace `v1.20.2-beta.1` in the `git checkout` line with that newer ref and resolve any 3-way conflicts Git reports.

## Quick verification after applying

```bash
uv run pytest tests/integration/test_proxy_anthropic_messages.py tests/unit/test_anthropic_messages_streaming.py -q
uv run ruff check app/core/openai/anthropic.py tests/integration/test_proxy_anthropic_messages.py tests/unit/test_anthropic_messages_streaming.py
```
