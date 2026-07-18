#!/usr/bin/env bash
# Pre-commit hook: fails the commit if backend/generated/openapi-schema.yaml or
# mobile/src/generated/schema.d.ts are stale relative to the current backend code.
#
# Regenerates both files (via scripts/generate-api.sh) and fails if that produces
# a diff against what's staged -- meaning the commit would otherwise ship a stale
# API contract. Requires the backend Docker containers to be running, since that's
# also true of generate-api.sh itself.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if ! (cd backend && docker-compose exec -T web true 2>/dev/null); then
  echo "error: backend Docker container ('web') isn't running or isn't reachable --"
  echo "can't verify the generated API files are up to date."
  echo "Start it with: cd backend && docker-compose up -d"
  exit 1
fi

./scripts/generate-api.sh > /dev/null

# Two distinct staleness signals are needed here:
#  1. Never staged at all -- `git diff` (worktree vs index) is silent about these,
#     since untracked files aren't in the index to diff against.
#  2. Staged, but regeneration produced something different from what's staged --
#     ordinary `git diff` (worktree vs index) catches this.
untracked="$(git ls-files --others --exclude-standard -- backend/generated mobile/src/generated)"
if [ -n "$untracked" ]; then
  echo
  echo "error: these generated files aren't staged yet:"
  echo "$untracked"
  echo "Review them, then: git add backend/generated mobile/src/generated"
  exit 1
fi

if ! git diff --exit-code -- backend/generated mobile/src/generated; then
  echo
  echo "error: backend/generated/openapi-schema.yaml or mobile/src/generated/schema.d.ts"
  echo "were stale and have been regenerated to match the current backend code (diff above)."
  echo "Review the changes, then: git add backend/generated mobile/src/generated"
  exit 1
fi

exit 0
