#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."

# Wave 6 operational verification. This intentionally requires Docker because
# the release contract includes a real PostgreSQL migration and a production
# Next.js build; SQLite or static mocks are not accepted as substitutes.

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is required for operational verification."
  echo "Run this script on a host with Docker Engine + Compose, or use GitHub Actions."
  exit 2
fi

export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-cinpassword}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-cinpassword}"
export REDIS_PASSWORD="${REDIS_PASSWORD:-cinpassword}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000/api/v1}"
export CIN_AUTH_API_KEYS="${CIN_AUTH_API_KEYS:-demo-submitter:submitter:b4058c303d0e54215e61317ccf704cb288a436181fd70c565051499c202d7837,demo-reviewer:reviewer:32dc90e9c2feb824612a5bd35883a01ba25a4555e173b3a31909a2f2,demo-steward:steward:0e9643da89a77a583192ca3a7fc1434c5861ba745a260605c72fd9c7d1f362f1}"

cleanup(){ docker compose down -v --remove-orphans >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo '== 1. Build and start infrastructure =='
docker compose up -d --build postgres redis neo4j

echo '== 2. Execute real PostgreSQL migration to head =='
docker compose run --rm migration alembic upgrade head

echo '== 3. Confirm Alembic head in PostgreSQL =='
docker compose run --rm api python - <<'PY'
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    e = create_async_engine(os.environ['DATABASE_URL'])
    async with e.connect() as c:
        row = (await c.execute(text('SELECT version_num FROM alembic_version'))).first()
        assert row and row[0] == '0017_wave6_future_intelligence', row
        print('POSTGRES_MIGRATION_HEAD_OK:', row[0])
    await e.dispose()

asyncio.run(main())
PY

echo '== 4. Build/start API and Web =='
docker compose up -d --build api web

echo '== 5. API readiness =='
curl --fail --retry 30 --retry-delay 2 http://localhost:8000/health/ready

echo
echo '== 6. Web readiness =='
curl --fail --retry 30 --retry-delay 2 http://localhost:3000/
echo

echo '== 7. Wave 6 behavioral tests =='
docker compose run --rm -e CIN_FAIL_ON_SKIP=1 -v "$PWD/tests:/app/tests:ro" -v "$PWD/pytest.ini:/app/pytest.ini:ro" -v "$PWD/apps/api/requirements-dev.txt:/app/requirements-dev.txt:ro" api sh -c 'pip install -q -r /app/requirements-dev.txt && pytest -q -rs tests/test_wave6_future_intelligence.py tests/test_wave5_question_alignment.py tests/test_wave4_question_knowledge.py tests/test_wave3_question_learning.py tests/test_wave2_question_intelligence.py'

echo
echo 'WAVE6_OPERATIONAL_VERIFY_OK'
