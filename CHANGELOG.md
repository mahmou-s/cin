
## Wave 6
- Future Intelligence + Scenario-Aware Questioning implemented and verified.
## Wave 6
- Added Future Intelligence + Scenario-Aware Questioning.
- Added future vision/horizon/scenario/readiness fields to client profiles.
- Added `CINFutureIntelligenceSignal` and migration 0017.
- Added future question ranking endpoint and deterministic guardrails.

# CIN v2.0 — Remediation Changelog

## Phase A — TASK 1 confidence gaps
- Source independence now groups by reviewer key, URL host, or one shared unknown group; SHA-256 is duplicate identity, not publisher independence.
- Ten distinct no-URL files are explicitly tested as one group.
- Raw confidence score and gate reasons are persisted beside the canonical gated score.
- HIGH requires two independent groups and two strong groups at or above 0.70.
- Confidence thresholds/cap/epsilon are configuration-driven and documented in ADR-005.
- Reviewer evidence assessments are stored in `evidence_assessments`.
- Migrations 0002–0005 added for independence, assessments, confidence audit/submission principal, and processing lease.
- Seed now uses two independent public-source hosts per key demo assertion and is explicitly labelled DEMO SEED.

## Phase B — TASK 2 reviewer identity
- Added bearer API-key authentication boundary with submitter/reviewer/steward roles.
- Reviewer identity comes from the authenticated principal, not request JSON.
- Self-review is rejected.
- Reviewer/steward-only review endpoint controls canonical assessments and independence keys.
- Web review/submission components send the bearer token from `localStorage.cin_api_token`.
- Security setup documented.

## Phase C — TASK 3 outbox recovery
- Redis enqueue failure after commit no longer converts a committed review into HTTP 500.
- PENDING outbox state remains durable and is returned to the client.
- Periodic reconciliation re-enqueues stale PENDING events and timed-out PROCESSING events.
- `processing_started_at` is persisted.
- Row-lock/status guard prevents duplicate delivery from claiming an already PROCESSING/PROCESSED event.

## Phase D — TASK 4 reasoning
- Added one shared chain-definition module for civilizational and path reasoning.
- Added canonical demo chain `C01 → C10 → C06 → C02`.
- Support now reports weakest-link and average using one documented aggregation policy.
- Documentation states reasoning reads PostgreSQL; Neo4j is currently projection/visualization.

## Phase E — TASK 5 behavioral tests
- Added behavioral integration coverage for confidence, review validation, transaction/outbox visibility, Redis-down review, reconciliation, crash recovery, duplicate delivery, self-review, and opportunity discovery.
- Contract tests remain only as a small supplementary layer.
- CI is configured to fail when pytest skips any test.

## Phase F — TASK 6 honest verification/docs
- README, SECURITY, production checklist, ADRs, CI and verify script now distinguish executed checks from unexecuted runtime verification.
- No GPU/NVIDIA performance result is claimed.

## Verification actually run in this environment
```text
PYTHON_COMPILE_OK
JS_SYNTAX_OK
VERIFY_SH_SYNTAX_OK
21 passed, 2 skipped in 0.41s
```

With `CIN_FAIL_ON_SKIP=1`:
```text
21 passed, 2 skipped in 0.37s
CIN_SKIP_POLICY_EXIT=1
```

The two skips are caused by unavailable `asyncpg` and `fakeredis`. Package installation could not reach the package index in this environment. Docker is also unavailable.

## Not run
- Real PostgreSQL migrations 0001→0002→0003→0004→0005 and downgrades against a live database.
- Real 422 endpoint tests against PostgreSQL/asyncpg.
- fakeredis behavioral tests.
- Real Redis delivery.
- Real Neo4j projection.
- Real seed run.
- Docker Compose runtime.
- Next.js production build.
- GPU/NVIDIA performance testing.


## Independent review remediation v2
- Hashed API-key authentication with production boot guards.
- All write endpoints authenticated; opportunity review actor comes from token.
- Reviewer-confirmed independence groups; derived URL/hash hints are non-canonical.
- Outbox single-attempt enqueue, timed reconcile, exponential backoff, steward dead-letter replay.
- Web token settings; no auth token in NEXT_PUBLIC_* build variables.
- Phase G embedding benchmark harness and Phase H pitch materials.
- Real Docker/Postgres/Redis/Neo4j/Next.js runtime verification remains environment-dependent.

## Data Model Hardening — 2026-09-25
- Added strict ActivityDomain, SupportType, and VerificationStatus enums.
- Converted profile activity domains and product support types to PostgreSQL typed arrays.
- Added product activity domain and verification status; profile verification status.
- Added explicit Product ↔ Evidence ORM association via product_evidence.
- Added evidence-derived AI confidence properties on Product and UserProfile; no manual confidence field is persisted for these profiles.
- Added InvestmentSupportRequest model and schemas.
- Added Pydantic business validation for agricultural land ownership and industrial factory/workshop tenure.
- Added migration 0008_data_model_hardening.

## API Product/Profile Integration — 2026-09-25
- Added authenticated `/api/v1/profiles/me` GET/POST/PATCH endpoints.
- Added authenticated product create/update endpoints under `/api/v1/profiles/me/products`.
- Added authenticated investment/support request creation for owned products.
- Evidence upload now persists an `Evidence` row and can link the evidence to an owned product using `product_id`.
- Evidence created by upload defaults to `__unknown_source__`; reviewer confirmation remains the canonical independence mechanism.
- Added tests for route coverage/auth dependency and evidence persistence/linking structure.
- Runtime PostgreSQL/asyncpg integration was not available in this environment.

## 2026-09-25 — Opportunity Discovery Layer
- Added Product → verified CapabilityAssertion linkage (`product_capability_assertions`).
- Added Opportunity → Product linkage (`opportunity_products`).
- Added `POST /api/v1/opportunities/discover/products` for evidence-grounded discovery.
- Discovery now operates on verified Products + verified CapabilityAssertions + verified Evidence, not UserProfile as the discovery unit.
- Opportunity rationale stores product IDs, capability assertion IDs, verified evidence IDs, capability pattern, and confidence floor for traceability.
- Added migration `0009_opportunity_product_links` and behavioral/unit coverage.

## Logistics Capability Domain (C11)
- Added product logistics profiles and logistics route records with verification status.
- Added evidence linkage for logistics routes.
- Added authenticated logistics API endpoints and homepage Logistics Intelligence panel.
- Added C11 capability seed and product-opportunity complementarity patterns for production, market, export, and external-connectivity + logistics.
- Added integration/contract tests for the logistics domain.

## Phase / Domain — Proactive Outreach (ADR-012)

- Implemented explicit user opt-in interest signals with idempotency on `(user_id, source_content_ref)`.
- Added durable outreach digest aggregation with per-external-entity cooldown.
- Reused the existing `Evidence` model for external contact channels using `EXTERNAL_CONTACT_CHANNEL`; new channels remain `PENDING` until verification.
- Added verified-channel delivery through an injectable sender interface; no real outbound email/API/social integration was added.
- Added identity protection so user identity is assembled for delivery only after a channel is `VERIFIED`.
- Added migration `0012_proactive_outreach.py`, API endpoint `POST /api/v1/outreach/signal`, service tests, and ADR-012; ADR-008 is marked superseded.
- **Checked in this environment:** Python compilation and pytest execution results are recorded with the release evidence; no claim is made for Docker/PostgreSQL/Redis production runtime unless actually executed.
- **Not executed in a real environment:** external email/contact-form/social delivery, production scheduler, Docker services, and live PostgreSQL/Redis/Neo4j integration where unavailable.


## Product positioning remediation (2026-09-27)

- Added `docs/PRODUCT_FOCUS.md` with narrowed commercial use cases, success metrics, and explicit non-claims.
- Rewrote `docs/pitch/one-page-brief.md` and `docs/pitch/10-slide-outline.md` to lead with product value instead of pure theory.
- Updated README purpose and Arabic subtitle to emphasize evidence-first matching + governed outreach; linked PRODUCT_FOCUS.
- Extended `docs/PRODUCTION_CHECKLIST.md` with prioritized product-critical next steps (docker runtime, E2E trust path, outreach E2E, focused pilot dataset, UX polish).
- Updated web home header to reflect v2.0 product positioning.

## E2E bootstrap (2026-09-27)

- Added `scripts/e2e_up.sh`: local full-stack bootstrap that keeps services running (env, compose up, migrate, seed, smoke checks).
- Added `scripts/e2e_down.sh`: clean stop without removing volumes by default.
- Added `docs/E2E_RUNBOOK.md`: Arabic/English quick-start and troubleshooting.
- Linked step 1 of PRODUCTION_CHECKLIST to the new E2E script.

## Runtime verification attempt + bugfixes (2026-09-27)

Attempted live E2E in constrained sandbox (1.2 GiB RAM).

### What succeeded
- PostgreSQL 16 + Redis 7 started natively.
- Neo4j 5.26 community started with reduced heap (256–384m).
- Alembic upgraded through `0012_proactive_outreach` after the fixes below.

### Bugs found and fixed in source
1. **Alembic `version_num` too short** — revision ids such as `0004_confidence_audit_and_submitter` exceed VARCHAR(32).
   - Fix: `migrations/env.py` ensures `alembic_version.version_num` is VARCHAR(128).
2. **Duplicate PostgreSQL ENUM creation** — migrations 0008 / 0010 / 0011 / 0012 re-created the same enum types when binding columns.
   - Fix: `create_type=False` + idempotent `DO $$ ... EXCEPTION WHEN duplicate_object` for shared enums.
3. **ImportError on API startup** — `scenarios.py` imported `_score` from `path_reasoning`, but it did not exist.
   - Fix: added `_score()` in `path_reasoning.py` using `aggregate_support` weakest-link.

### What did not complete in this environment
- Docker containers failed (`overlay upperdir not supported` nested mount).
- Full API readiness + seed + Neo4j projection smoke was interrupted by environment memory/reset limits.
- Next.js web UI was not started (RAM).

Run `./scripts/e2e_up.sh` on a machine with Docker and ≥4 GiB RAM for the full stack.


## 2026-10-02 — CIN 1 Master Roadmap / Institutional Intelligence
- Added `docs/CIN_MASTER_UPDATE_PLAN.md` as the controlling roadmap for the next CIN evolution.
- Added ADR-013 for BlackRock/German asset-management/Artisan institutional benchmarking.
- Added ADR-014 for Adaptive Choice-First Question Intelligence and governed question learning.
- Added ADR-015 for autonomous AI workforce / agent architecture.
- Added ADR-016 for institutional client intelligence profiles.
- Added a primary-source registry for BlackRock, Artisan, DWS, Union Investment, Deka and later institutions.
- No existing canonical truth, confidence semantics, or consent-gated outreach rule was relaxed.
- These new tracks are design/planning scope; they are not claimed as fully implemented in this package.

## Wave 3 — Question Learning & Governance
- Added governed recurring-pattern detection for user answers.
- Added candidate question generation with multi-session thresholds.
- Added reviewer approve/reject workflow for candidate questions.
- Added review metadata and pattern-generation metadata.
- Preserved the invariant: raw answers never auto-activate production questions.

## Wave 4
- Added CIN Question Knowledge Graph projection.
- Added evidence-aware, explainable question prioritization.
- Added priority-signal audit records and ranking endpoints.
- Added migration 0015.

## Wave 5 — Question Intelligence Alignment
- Added capability/evidence/opportunity/need/risk-aware next-question ranking.
- Added `CINQuestionIntelligenceSignal` and migration `0016_question_intelligence_alignment`.
- Enhanced answer progression and ranking endpoint with explainable intelligence signals.
- Added ADR-018 and Wave 5 implementation report.

## Wave 6 operational verification hardening
- Added `scripts/verify-wave6-operational.sh` for real PostgreSQL + Next.js operational verification.
- Added CI `web-build` job using Node 20 and `npm install` + `npm run build`.
- Added `docs/WAVE-6-OPERATIONAL-VERIFICATION.md`.
- Fixed Next.js client directive placement in `apps/web/app/page.js`.

## 2026-10-02 — Engineering Stabilization Audit
- Added `docs/ENGINEERING_STABILIZATION_AUDIT.md`.
- Added `docs/TECHNICAL_DEBT_REGISTER.md`.
- Added `docs/TEAM_AND_HOSTING_REQUIREMENTS.md`.
- Added `docs/CIN_ENGINEERING_BASELINE.md`.
- Added `scripts/audit-structure.sh`.
- Froze Wave 6 as the engineering baseline; no new production Wave should bypass P0 staging verification.

## 2026-10-03 — Staging Execution Gate
- Added `docs/STAGING_EXECUTION_RUNBOOK.md`.
- Added `scripts/staging_preflight.sh` to fail clearly when Docker/Compose/daemon is unavailable.
- Added `verification/STAGING-EXECUTION-REPORT.md` with the actual runtime boundary and evidence.
- Added a hard gate: no Wave 7 advancement or production-readiness claim before real staging runtime evidence.

## CI Runtime Verification — Real Staging E2E
- Replaced the false-positive staging validation pattern with a real Docker Compose runtime job.
- CI now starts PostgreSQL, Redis, Neo4j, Alembic migration, API, workers, outreach worker, and Next.js.
- CI verifies Alembic head `0017_wave6_future_intelligence` in PostgreSQL.
- CI verifies API readiness including all three infrastructure dependencies.
- CI verifies Next.js runtime availability.
- CI executes real Client Intelligence profile creation, question-session creation, question ranking, future ranking, and an answer transaction.
- CI verifies worker processes are running and application data is persisted in PostgreSQL.
- CI uploads staging logs and runtime evidence as artifacts.
