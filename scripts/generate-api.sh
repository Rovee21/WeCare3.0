#!/usr/bin/env bash
# Regenerates backend/generated/openapi-schema.yaml and mobile/src/generated/schema.d.ts.
# Everything runs inside Docker containers -- nothing is installed on the host.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Regenerating backend/generated/openapi-schema.yaml (requires backend containers running: docker-compose up -d)"
(cd "$REPO_ROOT/backend" && docker-compose exec -T web python manage.py spectacular --file generated/openapi-schema.yaml)

echo "==> Regenerating mobile/src/generated/schema.d.ts"
docker run --rm \
  -v "$REPO_ROOT:/repo" \
  -w /repo/mobile \
  -u "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  node:20-alpine \
  npm run generate:api

echo "Done."
