#!/usr/bin/env bash
# Thin entry point — all the orchestration logic lives in run.mjs (plain JS, no build step).
set -euo pipefail
exec node "$(dirname "${BASH_SOURCE[0]}")/run.mjs" "$@"
