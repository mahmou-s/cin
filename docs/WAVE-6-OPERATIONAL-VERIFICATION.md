# Wave 6 — Operational Verification Contract

## Purpose

Wave 6 is only considered operationally verified when both of these are executed against real services:

1. Alembic migration `0017_wave6_future_intelligence` against PostgreSQL 16.
2. Production Next.js build and runtime health check.

SQLite, mocked PostgreSQL, or static source inspection do not replace either check.

## Local / Docker command

```bash
./scripts/verify-wave6-operational.sh
```

The script:

- starts PostgreSQL, Redis, and Neo4j with Docker Compose;
- executes `alembic upgrade head`;
- reads `alembic_version` from PostgreSQL and requires `0017_wave6_future_intelligence`;
- builds and starts the API and Web services;
- checks `/health/ready` and the Web root;
- runs the Wave 2–6 behavioral tests;
- exits non-zero on any failure.

## CI contract

The repository CI now contains a dedicated `web-build` job using Node 20 and `npm ci`, followed by `npm run build`. The existing PostgreSQL service job continues to exercise real Alembic migrations.

## Current environment limitation

The execution environment used for the Wave 6 handoff does not expose Docker Engine/Compose and does not have a local PostgreSQL server. Therefore the real-service checks cannot honestly be marked as executed here. The repository now contains an executable operational verification contract so the checks run automatically in CI or on any Docker-enabled host.
