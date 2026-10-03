#!/usr/bin/env bash
# CIN v2.0 — simplified end-to-end bootstrap
# Starts the full stack, waits for readiness, seeds demo data, runs smoke checks.
# The stack REMAINS UP after this script (unlike scripts/verify.sh which tears down).
set -Eeuo pipefail
cd "$(dirname "$0")/.."

REPORT="${E2E_REPORT:-e2e_report.txt}"
: > "$REPORT"
exec > >(tee -a "$REPORT") 2>&1

echo "=============================================="
echo " CIN v2.0 — E2E bootstrap"
echo " $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=============================================="

# --- Local demo defaults (override via environment or .env) ---
export POSTGRES_DB="${POSTGRES_DB:-cin}"
export POSTGRES_USER="${POSTGRES_USER:-cin}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-cin-local-dev-password}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-cin-local-dev-password}"
export REDIS_PASSWORD="${REDIS_PASSWORD:-cin-local-dev-password}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000/api/v1}"
export API_PORT="${API_PORT:-8000}"
export WEB_PORT="${WEB_PORT:-3000}"
export APP_ENVIRONMENT="${APP_ENVIRONMENT:-development}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Demo API keys: principal:role:sha256(raw_key)
# Raw keys used only for local seed/demo (never for production).
export CIN_AUTH_API_KEYS="${CIN_AUTH_API_KEYS:-demo-submitter:submitter:b4058c303d0e54215e61317ccf704cb288a436181fd70c565051499c202d7837,demo-reviewer:reviewer:32dc90f8d497d0e9c2feb824612a5bd35883a01ba25a4555e173b3a31909a2f2,demo-steward:steward:0e9643da89a77a583192ca3a7fc1434c5861ba745a260605c72fd9c7d1f362f1}"
export CIN_DEMO_SUBMITTER_API_KEY="${CIN_DEMO_SUBMITTER_API_KEY:-demo-submitter-key}"
export CIN_DEMO_REVIEWER_API_KEY="${CIN_DEMO_REVIEWER_API_KEY:-demo-reviewer-key}"
export CIN_DEMO_STEWARD_API_KEY="${CIN_DEMO_STEWARD_API_KEY:-demo-steward-key}"

# Write a local .env if missing (so docker compose picks up values consistently)
if [[ ! -f .env ]]; then
  echo "== writing local .env from demo defaults =="
  cat > .env <<EOF
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
NEO4J_PASSWORD=${NEO4J_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}
CORS_ORIGINS=${CORS_ORIGINS}
NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
API_PORT=${API_PORT}
WEB_PORT=${WEB_PORT}
APP_ENVIRONMENT=${APP_ENVIRONMENT}
LOG_LEVEL=${LOG_LEVEL}
CIN_AUTH_API_KEYS=${CIN_AUTH_API_KEYS}
CIN_DEMO_SUBMITTER_API_KEY=${CIN_DEMO_SUBMITTER_API_KEY}
CIN_DEMO_REVIEWER_API_KEY=${CIN_DEMO_REVIEWER_API_KEY}
CIN_DEMO_STEWARD_API_KEY=${CIN_DEMO_STEWARD_API_KEY}
CONFIDENCE_COMBINED_SUPPORT_CAP=0.90
CONFIDENCE_HIGH_MIN_GROUP_SCORE=0.70
CONFIDENCE_HIGH_SCORE_THRESHOLD=0.85
CONFIDENCE_HIGH_MIN_INDEPENDENT_GROUPS=2
OUTBOX_RECONCILE_INTERVAL_SECONDS=30
OUTREACH_RECONCILE_INTERVAL_SECONDS=60
PROCESSING_TIMEOUT_SECONDS=900
EOF
  echo "Created .env (local demo only — do not use these secrets in production)."
else
  echo "== using existing .env =="
fi

command -v docker >/dev/null 2>&1 || { echo "ERROR: docker not found in PATH"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERROR: docker compose not available"; exit 1; }

echo ""
echo "== [1/6] Starting infrastructure (postgres, redis, neo4j) =="
docker compose up -d --build postgres redis neo4j

echo ""
echo "== [2/6] Waiting for infrastructure health =="
for i in $(seq 1 60); do
  pg=$(docker compose ps postgres --format '{{.Health}}' 2>/dev/null || echo "unknown")
  rd=$(docker compose ps redis --format '{{.Health}}' 2>/dev/null || echo "unknown")
  nj=$(docker compose ps neo4j --format '{{.Health}}' 2>/dev/null || echo "unknown")
  echo "  attempt $i: postgres=$pg redis=$rd neo4j=$nj"
  if [[ "$pg" == "healthy" && "$rd" == "healthy" && "$nj" == "healthy" ]]; then
    break
  fi
  sleep 3
done

echo ""
echo "== [3/6] Running Alembic migrations =="
docker compose run --rm migration alembic upgrade head

echo ""
echo "== [4/6] Starting API, Worker, Outreach Worker, Web =="
docker compose up -d --build api worker outreach_worker web

echo ""
echo "== [5/6] Waiting for API readiness =="
READY=0
for i in $(seq 1 45); do
  if curl -sf "http://localhost:${API_PORT}/health/ready" >/tmp/cin_ready.json 2>/dev/null; then
    echo "  API ready:"
    cat /tmp/cin_ready.json
    echo ""
    READY=1
    break
  fi
  echo "  waiting for /health/ready ($i)..."
  sleep 3
done
if [[ "$READY" != "1" ]]; then
  echo "ERROR: API did not become ready. Recent API logs:"
  docker compose logs --tail=80 api || true
  exit 1
fi

echo ""
echo "== [6/6] Seeding demo civilization data =="
docker compose run --rm --no-deps \
  -e DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}" \
  -e CIN_DEMO_SUBMITTER_API_KEY \
  -e CIN_DEMO_REVIEWER_API_KEY \
  -e CIN_DEMO_STEWARD_API_KEY \
  -v "$PWD/seed_civilization.py:/seed_civilization.py:ro" \
  api python /seed_civilization.py --api "http://api:8000/api/v1" --wait 8 || {
    echo "WARNING: seed returned non-zero. Continuing with smoke checks."
  }

echo ""
echo "== Smoke checks =="
fail=0

echo -n "  GET /health ... "
if curl -sf "http://localhost:${API_PORT}/health" | grep -q '"status":"ok"'; then
  echo "OK"
else
  echo "FAIL"; fail=1
fi

echo -n "  GET /health/ready ... "
if curl -sf "http://localhost:${API_PORT}/health/ready" | grep -q '"status":"ready"'; then
  echo "OK"
else
  echo "FAIL"; fail=1
fi

echo -n "  Web UI (port ${WEB_PORT}) ... "
if curl -sf "http://localhost:${WEB_PORT}" >/dev/null 2>&1; then
  echo "OK"
else
  echo "WARN (web may still be building)"
fi

echo -n "  Neo4j CapabilityAssertion count ... "
COUNT=$(docker compose exec -T neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (a:CapabilityAssertion) RETURN count(a) AS c;" 2>/dev/null | tr -d '\r' | grep -E '^[0-9]+$' | head -1 || echo "n/a")
echo "$COUNT"

echo ""
echo "=============================================="
if [[ "$fail" == "0" ]]; then
  echo " E2E_OK — stack is UP"
else
  echo " E2E_PARTIAL — stack is UP but some checks failed"
fi
echo "=============================================="
echo ""
echo "  API:     http://localhost:${API_PORT}"
echo "  Health:  http://localhost:${API_PORT}/health/ready"
echo "  Web UI:  http://localhost:${WEB_PORT}"
echo "  Neo4j:   http://localhost:7474  (user: neo4j)"
echo ""
echo "  Demo API keys (local only):"
echo "    submitter: \$CIN_DEMO_SUBMITTER_API_KEY"
echo "    reviewer:  \$CIN_DEMO_REVIEWER_API_KEY"
echo "    steward:   \$CIN_DEMO_STEWARD_API_KEY"
echo ""
echo "  Stop stack:  ./scripts/e2e_down.sh"
echo "  Full verify: ./scripts/verify.sh  (tears down on exit)"
echo "  Report:      $REPORT"
echo ""

exit "$fail"
