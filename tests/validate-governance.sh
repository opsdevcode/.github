#!/usr/bin/env bash
# Lightweight validation: syntax, profile JSON, no mutating GitHub verbs.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0

bash -n "$ROOT/scripts/audit-github-governance.sh"
bash -n "$ROOT/tests/validate-governance.sh"
python3 -m py_compile "$ROOT/scripts/github_governance_audit.py"

python3 - << PY
import json
from pathlib import Path
root = Path("$ROOT")
classes = json.loads((root / "profiles/classes.json").read_text())
assigns = json.loads((root / "profiles/assignments.json").read_text())
assert "A" in classes["classes"] and "F" in classes["classes"]
names = {r["name"] for r in assigns["repos"]}
required = {
    "repave", "overpass", "toll", "dispatch", "relay",
    "repave-aws-infra", "opdevcode-website", "convergence", ".github",
}
missing = required - names
assert not missing, missing
for row in assigns["repos"]:
    assert row["profile"] in classes["classes"], row
print("profiles parse OK")
PY

# Mutating HTTP must not appear in the audit implementation.
if grep -EIq -- '--method|-X POST|-X PUT|-X PATCH|-X DELETE|method POST|method PUT|method PATCH|method DELETE' \
  "$ROOT/scripts/audit-github-governance.sh" "$ROOT/scripts/github_governance_audit.py"; then
  echo "mutating gh flags found in audit implementation" >&2
  fail=1
fi
if grep -EIq '"POST"|"PUT"|"PATCH"|"DELETE"|'\''POST'\''|'\''PUT'\''|'\''PATCH'\''|'\''DELETE'\''' \
  "$ROOT/scripts/github_governance_audit.py"; then
  echo "mutating HTTP method literals found in audit implementation" >&2
  fail=1
fi

"$ROOT/scripts/audit-github-governance.sh" --offline

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi
echo "validate-governance: OK"
