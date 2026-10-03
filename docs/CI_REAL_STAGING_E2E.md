# CIN — Real Staging E2E CI Contract

The previous staging step only verified that infrastructure containers became healthy. That is insufficient to claim application integration or E2E success.

The new `staging-runtime-e2e` job is a blocking gate after the unit/migration suite and web build.

## Required runtime chain

PostgreSQL + Redis + Neo4j → Alembic head → API → Workers → Next.js → real HTTP transactions → PostgreSQL persistence.

## Blocking assertions

1. Docker and Compose are available.
2. PostgreSQL, Redis and Neo4j become healthy.
3. The migration container completes successfully.
4. PostgreSQL reports Alembic head `0017_wave6_future_intelligence`.
5. API `/health/ready` is ready and reports PostgreSQL/Redis/Neo4j as OK.
6. Next.js is reachable on port 3000.
7. Client Intelligence profile creation succeeds.
8. Question session creation succeeds.
9. Standard question ranking succeeds.
10. Future question ranking succeeds.
11. A choice or free-text answer is persisted through the real API.
12. Worker and outreach-worker containers are actually running.
13. Profile and question-session rows are persisted in PostgreSQL.

Any failure causes the workflow to fail. A log message such as `All staging services validated successfully` is never sufficient by itself.

## Evidence

The job uploads Docker Compose logs, service state, and the JSON responses produced by the real API flow as a workflow artifact named `cin-staging-e2e-report`.
