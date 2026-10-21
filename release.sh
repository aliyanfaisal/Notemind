#!/usr/bin/env bash
# Build the release zip, named with the version from .claude-plugin/plugin.json.
#   ./release.sh            ->  dist/notemind-v<version>.zip
#   ./release.sh --publish  ->  also tag v<version>, push, and attach the zip to a GitHub Release
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
VERSION="$(python3 -c 'import json; print(json.load(open(".claude-plugin/plugin.json"))["version"])')"
OUT="dist/notemind-v${VERSION}.zip"
claude plugin validate . >/dev/null
mkdir -p dist
rm -f "$OUT"
zip -qr "$OUT" .claude-plugin skills hooks scripts core assets docs LICENSE README.md \
  -x "*/__pycache__/*" "*/tests/*" "*.pyc" ".DS_Store" "*/.DS_Store"
echo "Built $OUT"

if [[ "${1:-}" == "--publish" ]]; then
  TAG="v${VERSION}"
  [[ -z "$(git status --porcelain)" ]] || { echo "Commit your changes before publishing." >&2; exit 1; }
  git rev-parse "$TAG" >/dev/null 2>&1 || git tag "$TAG"
  git push origin HEAD "$TAG"
  gh release create "$TAG" "$OUT" --title "Notemind $TAG" --generate-notes
  echo "Published $TAG with $OUT"
fi
