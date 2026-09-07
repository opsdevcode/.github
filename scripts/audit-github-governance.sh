#!/usr/bin/env bash
# Read-only OpsDevCode repository governance audit (gh api GET only).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh is required" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 2
fi

offline=0
for arg in "$@"; do
  if [[ "$arg" == "--offline" || "$arg" == "--validate" ]]; then
    offline=1
  fi
done
if [[ "$offline" -eq 0 ]]; then
  if ! gh auth status >/dev/null 2>&1; then
    echo "gh is not authenticated; run: gh auth login" >&2
    exit 2
  fi
fi

exec python3 "$ROOT/scripts/github_governance_audit.py" "$@"
