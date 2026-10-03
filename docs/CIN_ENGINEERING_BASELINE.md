# CIN Engineering Baseline

## Purpose
This file freezes the current engineering baseline after Wave 6. It is the handoff contract for any external engineering team.

## Product core
CIN is a decision/intelligence platform connecting people, organizations, capabilities, evidence, needs, opportunities, risks, scenarios and future readiness.

## Production-critical core
- Authentication/authorization boundary.
- PostgreSQL system of record.
- Evidence and confidence model.
- Human review gate.
- Transactional outbox.
- Neo4j projection.
- Opportunity discovery.
- Question intelligence.
- Future intelligence.
- API health/readiness.
- Web application.

## Research / controlled expansion
- Institutional benchmarking.
- BlackRock/German asset-manager lessons.
- Artisan-inspired AI workforce.
- Advanced autonomous agents.
- Additional semantic learning.

Research features must not weaken the evidence, authorization or human-review boundaries.

## Current migration head
`0017_wave6_future_intelligence`

## Current verification state
- Source compilation: PASS.
- Local behavioral tests with `PYTHONPATH=.`: 78 PASS, 7 SKIP.
- Real PostgreSQL runtime: NOT CERTIFIED in this environment.
- Real Redis runtime: NOT CERTIFIED in this environment.
- Real Neo4j runtime: NOT CERTIFIED in this environment.
- Docker Compose runtime: NOT CERTIFIED in this environment.
- Production Next.js runtime: NOT CERTIFIED in this environment.

## Handoff rule
No external team should treat skipped infrastructure checks as passed checks. The team must execute them in staging and attach logs/artifacts to the release record.
