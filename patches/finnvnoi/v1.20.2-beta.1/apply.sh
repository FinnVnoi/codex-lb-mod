#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
patch_file="$script_dir/0001-finnvnoi-local-mods-v1.20.2-beta.1.patch"

if [[ ! -f "$patch_file" ]]; then
  echo "Patch file not found: $patch_file" >&2
  exit 1
fi

if [[ "${1:-}" == "--check" ]]; then
  git apply --check --3way "$patch_file"
  echo "Patch applies cleanly (or with available 3-way base)."
  exit 0
fi

git apply --3way "$patch_file"
echo "Applied FinnVnoi codex-lb local patch bundle."
