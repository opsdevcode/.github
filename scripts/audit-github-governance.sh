#!/usr/bin/env bash
# Read-only OpsDevCode repository governance audit.
# Uses `gh api` GET only. Does not change GitHub settings.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh is required (https://cli.github.com/)" >&2
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to parse profile JSON" >&2
  exit 2
fi

if [[ "${1:-}" != "--offline" ]]; then
  if ! gh auth status >/dev/null 2>&1; then
    echo "gh is not authenticated; run: gh auth login" >&2
    exit 2
  fi
fi

exec python3 "$ROOT/scripts/github_governance_audit.py" "$@"
