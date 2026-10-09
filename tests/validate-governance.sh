#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bash -n "$ROOT/scripts/audit-github-governance.sh"
python3 "$ROOT/tests/test_governance.py" -q
"$ROOT/scripts/audit-github-governance.sh" --offline
"$ROOT/scripts/audit-github-governance.sh" --validate
bash "$ROOT/tests/validate-portfolio.sh"
python3 "$ROOT/tests/test_brand.py" -q
python3 "$ROOT/tests/test_release.py" -q
python3 "$ROOT/scripts/validate_release_contract.py" \
  --contract "$ROOT/opsdevcode-release.json" \
  --classification "$ROOT/profiles/releases.json"
echo "validate-governance: OK"
