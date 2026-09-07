#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -m json.tool "$ROOT/portfolio/products.json" >/dev/null
python3 "$ROOT/tests/test_portfolio.py" -q
echo "validate-portfolio: OK"
