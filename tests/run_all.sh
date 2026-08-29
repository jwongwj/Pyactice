#!/usr/bin/env bash
# Full test suite for the practice rig.
#
#   tests/run_all.sh
#
# Three layers, cheapest first:
#   1. structural   the problem bank's own self-check
#   2. backend      every HTTP endpoint, its payload shape, and its failure paths
#   3. browser      real Chrome, asserting on element geometry as well as content
#
# Layers 2 and 3 move sessions/ and workspace/ aside and restore them afterwards,
# so running this during a live attempt will not cost you your work.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
PY="${PFS_PYTHON:-python3}"
# No bytecode anywhere in the suite: the layers each clear __pycache__ and
# then import the bank, and that raced. See tests/api_test.py.
export PYTHONDONTWRITEBYTECODE=1
BACKUP="$(mktemp -d)"
FAILED=0

restore() {
  rm -rf "$REPO/sessions" "$REPO/workspace"
  [ -d "$BACKUP/sessions" ] && cp -R "$BACKUP/sessions" "$REPO/" 2>/dev/null
  [ -d "$BACKUP/workspace" ] && cp -R "$BACKUP/workspace" "$REPO/" 2>/dev/null
  rm -rf "$BACKUP"
}
trap restore EXIT

[ -d sessions ] && cp -R sessions "$BACKUP/" 2>/dev/null
[ -d workspace ] && cp -R workspace "$BACKUP/" 2>/dev/null

banner() { printf '\n\033[1m── %s\033[0m\n\n' "$1"; }

banner "1/3  problem bank"
if ! "$PY" -m harness validate; then FAILED=1; fi

banner "2/3  backend"
if ! "$PY" tests/api_test.py; then FAILED=1; fi

banner "3/3  browser"
if [ ! -d tests/node_modules ]; then
  echo "  installing puppeteer-core (drives your installed Chrome; no download)…"
  (cd tests && npm install --silent puppeteer-core@21 >/dev/null 2>&1)
fi
if ! node tests/ui.test.js; then FAILED=1; fi

if [ "$FAILED" -eq 0 ]; then
  printf '\n\033[32m\033[1mall suites passed\033[0m\n\n'
else
  printf '\n\033[31m\033[1mfailures above\033[0m\n\n'
fi
exit $FAILED
