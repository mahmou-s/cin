# Production Readiness Checklist

## Actually executed in the current environment

- [x] Python source compilation
- [x] Focused source-level pytest suite
- [x] JavaScript syntax checks for changed web components
- [x] Alembic offline SQL generation checks
- [x] CI skip-failure policy verified locally (`CIN_FAIL_ON_SKIP=1` exits 1 when integration dependencies are absent)

## Not executed in the current environment

- [ ] Real PostgreSQL migration execution, including pre-existing rows
- [ ] Real 0001 → 0002 → 0003 upgrade and downgrade against PostgreSQL
- [ ] Real endpoint 422 tests against PostgreSQL/asyncpg
- [ ] fakeredis behavioral tests
- [ ] Redis authentication and queue delivery
- [ ] Neo4j projection
- [ ] Full seed-to-graph integration test
- [ ] `docker compose up` runtime verification
- [ ] Next.js production build
- [ ] Backup/restore drill
- [ ] TLS termination and domain routing
- [ ] Secret management outside environment configuration
- [ ] Load/resource testing
- [ ] Production security/vulnerability scanning

A release must not be labelled fully production-certified until the staging
items above are executed and recorded.

## Prioritized next steps (product-critical)

1. **Full docker-compose runtime** — run `./scripts/e2e_up.sh` (see `docs/E2E_RUNBOOK.md`). Brings up Postgres + Redis + Neo4j + migration + API + Workers + Web, seeds demo data, smoke-checks health.
2. **End-to-end trust path** — submit assertion → review → outbox → Neo4j projection → opportunity path visible in UI.
3. **Proactive Outreach E2E** — explicit signal → digest → channel verification → injectable delivery (still no real external sender required).
4. **One focused pilot dataset** — single geography + single vertical with real verified capability nodes (see `docs/PRODUCT_FOCUS.md`).
5. **Next.js production build** and basic Human-Review / Opportunity-Review UX polish.
6. Only after the above: load testing, TLS, backup/restore, security scanning.

## Automation

`scripts/verify.sh` is the end-to-end local verification entry point. GitHub
Actions provisions PostgreSQL, runs the migration round-trip with pre-existing
rows, and runs the behavioral pytest suite. CI is configured to fail if any
test is skipped.

No GPU/NVIDIA performance benchmark or performance result is part of this
release.
