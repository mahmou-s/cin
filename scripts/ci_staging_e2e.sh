#!/usr/bin/env bash
# CIN CI — real staging runtime + application E2E.
# This script MUST fail if only infrastructure is healthy but the application is not.
set -Eeuo pipefail
cd "$(dirname "$0")/.."

export POSTGRES_DB=cin
export POSTGRES_USER=cin
export POSTGRES_PASSWORD=ci-postgres-password
export NEO4J_PASSWORD=ci-neo4j-password
export REDIS_PASSWORD=ci-redis-password
export CORS_ORIGINS=http://localhost:3000
export NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
export API_PORT=8000
export WEB_PORT=3000
export APP_ENVIRONMENT=staging
export LOG_LEVEL=INFO
export CIN_AUTH_API_KEYS='ci-submitter:submitter:b4058c303d0e54215e61317ccf704cb288a436181fd70c565051499c202d7837,ci-reviewer:reviewer:32dc90f8d4970e9c2feb824612a5bd35883a01ba25a4555e173b3a31909a2f2,ci-steward:steward:0e9643da89a77a583192ca3a7fc1434c5861ba745a260605c72fd9c7d1f362f1'
export CIN_DEMO_SUBMITTER_API_KEY=ci-submitter-key
export CIN_DEMO_REVIEWER_API_KEY=ci-reviewer-key
export CIN_DEMO_STEWARD_API_KEY=ci-steward-key

cat > .env <<ENV
POSTGRES_DB=$POSTGRES_DB
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
NEO4J_PASSWORD=$NEO4J_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
CORS_ORIGINS=$CORS_ORIGINS
NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
API_PORT=$API_PORT
WEB_PORT=$WEB_PORT
APP_ENVIRONMENT=$APP_ENVIRONMENT
LOG_LEVEL=$LOG_LEVEL
CIN_AUTH_API_KEYS=$CIN_AUTH_API_KEYS
CIN_DEMO_SUBMITTER_API_KEY=$CIN_DEMO_SUBMITTER_API_KEY
CIN_DEMO_REVIEWER_API_KEY=$CIN_DEMO_REVIEWER_API_KEY
CIN_DEMO_STEWARD_API_KEY=$CIN_DEMO_STEWARD_API_KEY
ENV

REPORT_DIR="${RUNNER_TEMP:-/tmp}/cin-staging-report"
mkdir -p "$REPORT_DIR"

cleanup() {
  docker compose logs --no-color > "$REPORT_DIR/docker-compose.log" 2>&1 || true
  docker compose ps > "$REPORT_DIR/docker-compose-ps.txt" 2>&1 || true
  docker compose down -v --remove-orphans || true
}
trap cleanup EXIT

fail() { echo "STAGING_E2E_FAIL: $*" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || fail "docker is unavailable"
docker compose version >/dev/null 2>&1 || fail "docker compose is unavailable"

# Infrastructure + migration + application runtime.
docker compose up -d --build postgres redis neo4j

echo "Waiting for infrastructure..."
for i in $(seq 1 60); do
  pg=$(docker compose ps postgres --format '{{.Health}}' 2>/dev/null || true)
  rd=$(docker compose ps redis --format '{{.Health}}' 2>/dev/null || true)
  nj=$(docker compose ps neo4j --format '{{.Health}}' 2>/dev/null || true)
  if [[ "$pg" == healthy && "$rd" == healthy && "$nj" == healthy ]]; then break; fi
  [[ "$i" == 60 ]] && fail "infrastructure did not become healthy: postgres=$pg redis=$rd neo4j=$nj"
  sleep 3
done

# Migration is executed by the real migration container, not merely imported by Python.
docker compose run --rm migration

VERSION=$(docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc 'SELECT version_num FROM alembic_version;')
[[ "$VERSION" == "0017_wave6_future_intelligence" ]] || fail "unexpected alembic head: $VERSION"
echo "Alembic head verified: $VERSION"

# Start every application service that production-like staging uses.
docker compose up -d --build api worker outreach_worker web

for i in $(seq 1 60); do
  api_health=$(docker compose ps api --format '{{.Health}}' 2>/dev/null || true)
  web_health=$(docker compose ps web --format '{{.Health}}' 2>/dev/null || true)
  if [[ "$api_health" == healthy && "$web_health" == healthy ]]; then break; fi
  [[ "$i" == 60 ]] && fail "application services did not become healthy: api=$api_health web=$web_health"
  sleep 3
done

# Real service checks from the host.
curl -fsS http://localhost:8000/health | grep -q '"status":"ok"' || fail "API /health failed"
READY=$(curl -fsS http://localhost:8000/health/ready)
echo "$READY" | grep -q '"status":"ready"' || fail "API readiness failed: $READY"
for dependency in postgres redis neo4j; do echo "$READY" | grep -q "\"$dependency\":\"ok\"" || fail "readiness missing $dependency"; done
curl -fsS http://localhost:3000 >/dev/null || fail "Next.js runtime is unreachable"

AUTH="Authorization: Bearer $CIN_DEMO_SUBMITTER_API_KEY"
CONTENT='Content-Type: application/json'

# Real Client Intelligence + adaptive question flow.
curl -fsS -X POST http://localhost:8000/api/v1/client-intelligence/me \
  -H "$AUTH" -H "$CONTENT" \
  -d '{"segment":"CORPORATION","organization_size":"MEDIUM","strategic_objectives":["growth"],"constraints":["capital"],"decision_horizon":"3Y","readiness_level":"MEDIUM","desired_future":"resilient growth","future_horizon":"3Y","preferred_scenarios":["GROWTH","STRESS"],"readiness_barriers":["capital"]}' \
  > "$REPORT_DIR/client-profile.json"

SESSION=$(curl -fsS -X POST http://localhost:8000/api/v1/questions/sessions \
  -H "$AUTH" -H "$CONTENT" -d '{"segment":"CORPORATION"}')
echo "$SESSION" > "$REPORT_DIR/question-session.json"
SESSION_ID=$(python -c 'import json,sys; print(json.load(sys.stdin)["session_id"])' <<< "$SESSION")
[[ -n "$SESSION_ID" ]] || fail "question session was not created"

RANK=$(curl -fsS -H "$AUTH" "http://localhost:8000/api/v1/questions/sessions/$SESSION_ID/ranking")
echo "$RANK" > "$REPORT_DIR/question-ranking.json"
FUTURE=$(curl -fsS -H "$AUTH" "http://localhost:8000/api/v1/questions/sessions/$SESSION_ID/future-ranking")
echo "$FUTURE" > "$REPORT_DIR/future-ranking.json"

QUESTION=$(python -c 'import json,sys; print(json.load(sys.stdin)["question"])' <<< "$SESSION")
OPTION=$(python -c 'import json,sys; q=json.loads(sys.stdin.read()); print((q.get("options") or [""])[0])' <<< "$QUESTION")
if [[ -n "$OPTION" ]]; then
  curl -fsS -X POST "http://localhost:8000/api/v1/questions/sessions/$SESSION_ID/answer" \
    -H "$AUTH" -H "$CONTENT" \
    -d "$(python -c 'import json,sys; print(json.dumps({"mode":"CHOICE","selected_option":sys.argv[1]}))' "$OPTION")" \
    > "$REPORT_DIR/question-answer.json"
else
  curl -fsS -X POST "http://localhost:8000/api/v1/questions/sessions/$SESSION_ID/answer" \
    -H "$AUTH" -H "$CONTENT" \
    -d '{"mode":"OTHER","free_text":"CI staging free-text answer"}' \
    > "$REPORT_DIR/question-answer.json"
fi

# Verify workers are actually running, not merely declared in compose.
for service in worker outreach_worker; do
  state=$(docker compose ps "$service" --format '{{.State}}' 2>/dev/null || true)
  [[ "$state" == running ]] || fail "$service is not running: $state"
done

# Assert the real migration state and that the API transaction wrote a profile/session.
PROFILE_COUNT=$(docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT count(*) FROM client_intelligence_profiles WHERE principal_id='ci-submitter';")
[[ "$PROFILE_COUNT" -ge 1 ]] || fail "client profile was not persisted"
SESSION_COUNT=$(docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT count(*) FROM cin_question_sessions WHERE id='$SESSION_ID';")
[[ "$SESSION_COUNT" == 1 ]] || fail "question session was not persisted"

echo "REAL_STAGING_E2E_OK"
echo "Artifacts: $REPORT_DIR"
