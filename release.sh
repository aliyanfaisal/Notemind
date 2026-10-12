#!/usr/bin/env bash
# Build the release zip, named with the version from .claude-plugin/plugin.json.
#   ./release.sh        ->  dist/notemind-v<version>.zip
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
VERSION="$(python3 -c 'import json; print(json.load(open(".claude-plugin/plugin.json"))["version"])')"
OUT="dist/notemind-v${VERSION}.zip"
claude plugin validate . >/dev/null
mkdir -p dist
rm -f "$OUT"
zip -qr "$OUT" .claude-plugin skills hooks scripts core assets LICENSE README.md \
  -x "*/__pycache__/*" "*/tests/*" "*.pyc" ".DS_Store" "*/.DS_Store"
echo "Built $OUT"
