#!/usr/bin/env bash
set -euo pipefail

# Build a clean distributable zip from the current working tree.
# Usage: ./scripts/build_release.sh v1.1.0

VERSION="${1:-dev}"
OUT="crowdlike-${VERSION}.zip"

echo "Cleaning known artifacts..."
rm -f .env bash.exe.stackdump crowdlike.db || true
rm -rf .crowdlike_data __pycache__ out lib cache || true
rm -rf _backup_* _archive_* || true
find . -name "__pycache__" -type d -prune -exec rm -rf {} + || true
find . -name "*.pyc" -type f -delete || true
find . -name "*.bak*" -type f -delete || true

echo "Creating zip (tracked files preferred if git is available)..."
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git archive --format=zip --output "$OUT" HEAD
else
  # Fallback: zip current directory excluding common junk
  zip -r "$OUT" . -x "*.pyc" "__pycache__/*" ".crowdlike_data/*" ".env" "out/*" "lib/*" "cache/*" "_backup_*/*" "_archive_*/*"
fi

echo "Wrote $OUT"
