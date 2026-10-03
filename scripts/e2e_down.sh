#!/usr/bin/env bash
# Stop the CIN E2E stack started by scripts/e2e_up.sh
set -Eeuo pipefail
cd "$(dirname "$0")/.."

echo "Stopping CIN stack..."
docker compose down
echo "Done. Volumes retained (pg_data, neo4j_data, redis_data, evidence_data)."
echo "To also remove volumes: docker compose down -v"
