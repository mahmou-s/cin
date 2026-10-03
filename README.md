# Civilizational Intelligence Network — v2.0 Production Demonstrator

**منصة الشبكة الحضارية العالمية — Evidence-first capability matching with governed outreach**

> **Product focus:** See [`docs/PRODUCT_FOCUS.md`](docs/PRODUCT_FOCUS.md) for the narrowed commercial positioning, primary use cases, and success metrics.

## Purpose

CIN is an **evidence-first capability matching platform**. It models communities and companies as **Capability Nodes**, validates capability assertions against evidence, projects verified facts into a Knowledge Graph, and derives explainable complementary opportunity paths. A tightly controlled Proactive Outreach workflow converts explicit user interest into consent-gated introductions.

The platform is deliberately designed so that:

- PostgreSQL is the **System of Record**.
- The transactional outbox is the authoritative integration boundary.
- Redis is a fast task-notification/queue layer, not a source of truth.
- Neo4j is a rebuildable Knowledge Graph projection.
- AI/analytical reasoning cannot promote unverified data to verified truth.
- Confidence measures evidence support; it is not a ranking, capability score, or probability of success.
- Opportunity paths are hypotheses for human review, not guarantees of willingness, feasibility, or outcomes.
- Outreach never starts from a passive view; it requires explicit user opt-in and a verified external contact channel.

## Production data path

```text
RAW DATA
   ↓
EVIDENCE
   ↓
VERIFIED FACT
   ↓
PostgreSQL
   ↓
Transactional Outbox
   ↓
Redis Queue
   ↓
Worker
   ↓
Neo4j Knowledge Graph
   ↓
Relations / Opportunity Paths / Scenarios
   ↓
Human Review
   ↓
Next.js Visualization
```

## Services

1. **Next.js** — interactive product UI and graph visualization.
2. **FastAPI** — API, validation and domain orchestration.
3. **PostgreSQL** — authoritative relational store.
4. **Neo4j** — graph intelligence projection.
5. **Redis** — reliable event-ID queue for low-latency projection.
6. **Alembic** — deterministic database schema migrations.
7. **Worker** — Redis-driven idempotent Neo4j projection.

## Database migration

The API container does not call `Base.metadata.create_all()` in production. Schema ownership belongs to Alembic.

```bash
cd apps/api
alembic upgrade head
```

Compose performs this automatically through the one-shot `migration` service before the API and Worker become ready.

## Redis / Outbox behavior

A verified assertion creates a PostgreSQL transactional-outbox event in the same database transaction as the verification decision. After the transaction commits, the API pushes the event ID to Redis.

The Worker consumes Redis with blocking `BLPOP`, loads the event from PostgreSQL, marks it `PROCESSING`, performs an idempotent Neo4j `MERGE`, then marks it `PROCESSED`.

If Redis delivery or the Worker fails, the PostgreSQL outbox remains authoritative. The Worker performs a bounded reconciliation scan at startup for `PENDING`/`PROCESSING` events. This is recovery, not continuous database polling.

## Start

```bash
cp .env.example .env
# edit .env

docker compose --env-file .env up --build -d
```

For a public cloud deployment, terminate TLS at the cloud load balancer/reverse proxy and set `NEXT_PUBLIC_API_URL` to the browser-reachable HTTPS API URL.

## Health

```bash
curl http://SERVER:8000/health
curl http://SERVER:8000/health/ready
```

Readiness checks PostgreSQL, Redis and Neo4j.

## Demonstrator seed

```bash
python3 seed_civilization.py --api https://api.example.com/api/v1
```

The demonstrator creates:

- **Community A — Egypt:** C01 Production + C10 External Connectivity.
- **Community B — Technology Region:** C06 Technology.
- **Community C — Financial & Market Center:** C02 Economic & Market.

The evidence is intentionally demonstrator material. It must be independently revalidated by an authorized data steward before being treated as authoritative research data.

The configured analytical path is:

```text
C01 Production
   → C10 External Connectivity
   → C06 Technology
   → C02 Economic & Market
```

This path represents analytical complementarity only. It does not imply willingness, investment advice, feasibility, or guaranteed success.

## NVIDIA technical positioning

The current release is **CPU-first and GPU-ready by architecture**. It does not claim CUDA performance or NVIDIA benchmark results.

Potential future accelerated workloads include:

- multilingual document understanding;
- entity/capability extraction;
- embeddings and hybrid retrieval;
- graph representation learning;
- large-scale scenario search;
- evidence classification.

See [`docs/NVIDIA_TECHNICAL_BRIEF.md`](docs/NVIDIA_TECHNICAL_BRIEF.md).

## Security boundary

This release is appropriate for a controlled technical demonstration and cloud-hosted MVP. Before unrestricted public exposure, complete OIDC/OAuth2, RBAC, rate limiting, TLS/HSTS, secret management, malware scanning, object storage, centralized audit logging, backups/restore testing, and container/dependency vulnerability scanning.

See [`SECURITY.md`](SECURITY.md).

## Validation performed for this package

The following checks were actually executed in the current environment:

- Python compilation: **PASS** — `PYTHON_COMPILE_OK`
- JavaScript syntax checks for the changed web components: **PASS** — `JS_SYNTAX_OK`
- Focused source-level tests: **PASS** — 16 passed
- Full local pytest collection/execution: **21 passed, 2 skipped**. The skips are
  integration tests requiring `asyncpg` and `fakeredis`, which are not installed
  and could not be downloaded in this environment.
- `CIN_FAIL_ON_SKIP=1 pytest`: **FAIL by design** with exit code 1 because the
  two integration tests were skipped.
- Alembic migration checks: **offline SQL generation only**; real PostgreSQL
  execution was not available.
- Docker runtime: **not executed** — Docker is unavailable in this environment.
- Next.js production build: **not executed**.
- Real seed-to-PostgreSQL/Redis/Neo4j run: **not executed**.

No NVIDIA hardware or GPU performance result is claimed by this release.

## Verification workflow

`scripts/verify.sh` is the local end-to-end verification entry point. It starts
Docker Compose, applies migrations, runs the full test suite with skip-failure
policy, runs the demo seed, and checks API health/readiness. GitHub Actions also
runs the PostgreSQL migration round-trip with pre-existing rows and the full
behavioral test suite; the CI configuration fails when any pytest test is
skipped.

## NVIDIA Technical Demonstrator package

This release separates the current deterministic/data architecture from future
accelerated-computing work. Any future NVIDIA/GPU integration must be supported
by controlled measurements before performance conclusions are made.

### Trust and data flow

`RAW DATA → EVIDENCE → VALIDATION → HUMAN REVIEW → VERIFIED FACT → POSTGRESQL → TRANSACTIONAL OUTBOX → REDIS → NEO4J → EXPLAINABLE OPPORTUNITY`

### Release status

The source-level portions verified here do not certify Docker deployment,
PostgreSQL runtime migrations, Redis delivery, Neo4j projection, the Next.js
production build, TLS, load testing, backup/restore, or production security
hardening. Those remain explicit verification tasks in
`docs/PRODUCTION_CHECKLIST.md`.

## Verification
Run `./scripts/verify.sh`. It writes all output to `verification_report.txt` and
fails when Docker, a dependency, or any skipped test prevents full verification.
The script does not remove volumes before saving the report.

## Phase G/H
`benchmarks/embedding_benchmark.py` contains a fake-model unit-test harness only;
`benchmarks/RESULTS.md` explicitly records that a real embedding benchmark was
NOT RUN. Presentation materials live under `docs/pitch/`.

## Product Network & Value Chain — V1

CIN now models an end-to-end product value chain in addition to capability and logistics intelligence.

Flow supported:

`Component Suppliers → Manufacturer → Exporter → Importer → Distributor/Agent → Retailer → Service Provider`

New concepts:
- `ProductComponent`: product-to-component composition, internal/external sourcing, quantity/unit, requirement and verification status.
- `ValueChainLink`: ordered relationship between participant profiles, optional source/target products, stage type and relationship type.
- Evidence join tables preserve traceability for component and value-chain claims.
- API: `GET /api/v1/value-chain/products/{product_id}` plus authenticated write endpoints for components and links.
- Ownership checks prevent a submitted chain from attributing a product to a different participant profile.

This is a **network representation**, not proof of a commercial contract. Investor-facing or operational decisions still require verification and human review.


## CIN Institutional Intelligence & Autonomous Workforce — Roadmap
The next evolution is governed by `docs/CIN_MASTER_UPDATE_PLAN.md`. It adds institutional intelligence benchmarking (BlackRock, selected German asset managers and Artisan), client-type adaptive questioning, governed question learning, risk/scenario/future intelligence, and a permissioned autonomous AI workforce. These are roadmap capabilities unless a module is explicitly marked implemented.

Primary-source registry: `docs/INSTITUTIONAL_INTELLIGENCE_SOURCE_REGISTRY.md`.
