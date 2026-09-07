#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bash -n "$ROOT/scripts/audit-github-governance.sh"
python3 "$ROOT/tests/test_governance.py" -q
"$ROOT/scripts/audit-github-governance.sh" --offline
"$ROOT/scripts/audit-github-governance.sh" --validate
echo "validate-governance: OK"
