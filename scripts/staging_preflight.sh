#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."

echo '== CIN staging preflight =='
command -v docker >/dev/null 2>&1 || { echo 'BLOCKED: Docker Engine is not installed/available.'; exit 2; }
docker compose version >/dev/null 2>&1 || { echo 'BLOCKED: Docker Compose v2 is not available.'; exit 2; }

docker info >/dev/null 2>&1 || { echo 'BLOCKED: Docker daemon is not running or not accessible.'; exit 2; }

echo 'Docker engine: OK'
echo 'Docker compose: OK'
echo 'Docker daemon: OK'
echo 'Next: ./scripts/e2e_up.sh'
