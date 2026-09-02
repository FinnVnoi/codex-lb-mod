#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
patch_file="$script_dir/0001-finnvnoi-production-snapshot.patch"
repo_root="$(git -C "$script_dir/../../.." rev-parse --show-toplevel)"
expected_base="4c0dbc9ceb2b5d70204ea7603cf1b4bef83db234"

if [[ ! -f "$patch_file" ]]; then
  echo "Patch file not found: $patch_file" >&2
  exit 1
fi

if ! git -C "$repo_root" cat-file -e "$expected_base^{commit}" 2>/dev/null; then
  echo "Required Codex-LB v1.22.0 base commit is unavailable: $expected_base" >&2
  exit 1
fi

case "${1:-}" in
  --check)
    git -C "$repo_root" apply --check "$patch_file"
    echo "Patch applies cleanly to the current checkout."
    ;;
  "")
    git -C "$repo_root" apply "$patch_file"
    echo "Applied FinnVnoi Codex-LB production patch snapshot."
    ;;
  *)
    echo "Usage: $0 [--check]" >&2
    exit 2
    ;;
esac
