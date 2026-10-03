# CIN Staging Environment — Execution Runbook

## Purpose

Run the complete CIN staging stack from the Engineering Stabilized baseline and produce evidence for PostgreSQL, Redis, Neo4j, API, workers, Next.js, and E2E behavior.

## Required host

- Docker Engine with Docker Compose v2
- Internet access to pull images and install build dependencies
- Minimum recommended: 4 CPU, 8 GB RAM, 30 GB free disk
- Git checkout or extracted release directory

## Start

```bash
cp .env.example .env
# replace every production-like secret in .env for the staging environment
./scripts/e2e_up.sh
```

## Required evidence

1. `docker compose ps` shows PostgreSQL, Redis, Neo4j, API, worker, outreach_worker and web healthy/running.
2. Alembic head in PostgreSQL is `0017_wave6_future_intelligence`.
3. `GET /health` returns OK.
4. `GET /health/ready` returns ready and dependency checks succeed.
5. Next.js production container serves `/`.
6. Worker logs show successful startup and no crash loop.
7. Outreach worker starts without crash loop.
8. Neo4j query returns a valid result after demo seed/projection.
9. Wave 2–6 tests pass with `CIN_FAIL_ON_SKIP=1`.
10. E2E smoke checks complete without a failed assertion.

## Stop and preserve logs

```bash
docker compose ps > verification/staging-compose-ps.txt
docker compose logs --no-color > verification/staging-compose.log
./scripts/e2e_down.sh
```

Do not use `docker compose down -v` until logs and database migration evidence have been collected.

## Production-readiness gate

A staging run is **PASS** only when all required evidence above exists. A source-code test run without Docker is not a staging pass.
