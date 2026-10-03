#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
REPORT="verification_report.txt"
: > "$REPORT"
exec > >(tee -a "$REPORT") 2>&1
export CIN_FAIL_ON_SKIP=1
export PYTHONPATH=.
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-cinpassword}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-cinpassword}"
export REDIS_PASSWORD="${REDIS_PASSWORD:-cinpassword}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000/api/v1}"
export CIN_AUTH_API_KEYS="${CIN_AUTH_API_KEYS:-demo-submitter:submitter:b4058c303d0e54215e61317ccf704cb288a436181fd70c565051499c202d7837,demo-reviewer:reviewer:32dc90f8d497d0e9c2feb824612a5bd35883a01ba25a4555e173b3a31909a2f2,demo-steward:steward:0e9643da89a77a583192ca3a7fc1434c5861ba745a260605c72fd9c7d1f362f1}"
export CIN_DEMO_SUBMITTER_API_KEY="${CIN_DEMO_SUBMITTER_API_KEY:-demo-submitter-key}"
export CIN_DEMO_REVIEWER_API_KEY="${CIN_DEMO_REVIEWER_API_KEY:-demo-reviewer-key}"
export CIN_DEMO_STEWARD_API_KEY="${CIN_DEMO_STEWARD_API_KEY:-demo-steward-key}"
cleanup(){ docker compose down; }
trap cleanup EXIT

echo '== docker compose up infrastructure =='
docker compose up -d --build postgres redis neo4j

echo '== alembic upgrade =='
docker compose run --rm migration alembic upgrade head

echo '== api/worker/web =='
docker compose up -d --build api worker web

echo '== health =='
curl --fail --retry 30 --retry-delay 2 http://localhost:8000/health/ready

echo '== full pytest (skip must fail) =='
docker compose run --rm -e CIN_FAIL_ON_SKIP=1 -v "$PWD/tests:/app/tests:ro" -v "$PWD/pytest.ini:/app/pytest.ini:ro" -v "$PWD/apps/api/requirements-dev.txt:/app/requirements-dev.txt:ro" api sh -c 'pip install -q -r /app/requirements-dev.txt && pytest -q -rs'

echo '== migration round-trip with pre-existing rows =='
docker compose run --rm api alembic downgrade 0001_initial_cin
docker compose run --rm migration alembic upgrade 0001_initial_cin
docker compose run --rm api python - <<'PY'
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
url=os.environ['DATABASE_URL']
async def main():
 e=create_async_engine(url)
 async with e.begin() as c:
  await c.execute(text("INSERT INTO communities (id,name,country_code,created_at) VALUES ('00000000-0000-0000-0000-000000000011','VERIFY pre-existing','EG',now()) ON CONFLICT DO NOTHING"))
 await e.dispose()
asyncio.run(main())
PY
docker compose run --rm migration alembic upgrade head

echo '== seed =='
docker compose run --rm --no-deps -e DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-cin}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-cin}" -e CIN_DEMO_SUBMITTER_API_KEY -e CIN_DEMO_REVIEWER_API_KEY -e CIN_DEMO_STEWARD_API_KEY -v "$PWD/seed_civilization.py:/seed_civilization.py:ro" api python /seed_civilization.py --api http://api:8000/api/v1 --wait 5

echo '== Neo4j projection count =='
docker compose exec -T neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" 'MATCH (a:CapabilityAssertion) RETURN count(a) AS capability_assertions;'

echo '== verification complete =='
echo 'VERIFY_OK'
