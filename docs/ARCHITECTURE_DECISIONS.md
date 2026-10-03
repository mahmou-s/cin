# CIN Architecture Decision Record

## ADR-001 — PostgreSQL is the System of Record

**Decision:** Canonical facts, evidence, validation events and transactional outbox records live in PostgreSQL.

**Reason:** Strong transactional semantics, auditability and deterministic recovery.

## ADR-002 — Redis is a delivery layer, not a source of truth

**Decision:** Redis contains event IDs only. It accelerates delivery from the outbox to the Worker.

**Reason:** Redis loss must not destroy canonical events.

## ADR-003 — Neo4j is a rebuildable projection

**Decision:** Neo4j contains the knowledge graph projection of verified facts.

**Reason:** Graph performance and traversal are separated from transactional persistence.

## ADR-004 — Human review gates canonical truth

**Decision:** SUBMITTED assertions cannot reach the canonical graph until review marks them VERIFIED.

**Reason:** Model extraction and analytical inference are not evidence verification.

## ADR-005 — Confidence is evidence support, not capability strength

**Decision:** `confidence_score` measures evidence support for an assertion. It must not be interpreted as community quality or capability ranking. Reviewer confidence is calculated from the strongest evidence per independent source group. Source groups are derived server-side from the URL host, then SHA-256, with a single shared `__unknown_source__` group when no source identity exists. A reviewer may explicitly override the source group in `evidence_assessments`.

**Policy thresholds:**
- `confidence_high_min_group_score = 0.70`: an independent group is strong enough for the HIGH gate only at or above this score.
- `confidence_combined_support_cap = 0.90`: combined noisy-OR support is capped at 0.90.
- HIGH additionally requires at least 2 independent groups at or above 0.70.
- If the raw score reaches the HIGH numeric threshold but the HIGH evidence gate is not satisfied, the stored score is capped below 0.85 so downstream consumers cannot mistake the number for HIGH confidence.

These values are configuration settings, not probabilities or measures of community quality. Every reviewer evidence assessment is stored in the `evidence_assessments` table; validation events retain an audit snapshot as well.

## ADR-006 — Opportunity is a hypothesis

**Decision:** Opportunity paths are analytical hypotheses derived from verified capabilities. They do not imply willingness, feasibility, financing, legal approval or guaranteed success.

## ADR-007 — GPU adoption is benchmark-driven

**Decision:** GPU acceleration is introduced only after a workload is measured and shown to benefit from acceleration.

**Reason:** NVIDIA positioning must be technically defensible rather than marketing-driven.

## ADR-008 — Proactive outreach is a signal-to-action capability, not yet implemented

**Superseded by ADR-012.** The decision-in-principle and open questions recorded here are resolved by ADR-012.

**Decision:** When CIN detects a genuine behavioral signal of user interest (e.g., a user watching a company's public video), the system MAY proactively notify that company, on the user's behalf, that the user viewed their offer. Two target types are supported:
1. Registered network members — notified through an internal API/notification channel.
2. External entities outside the network — notified through a discovered public contact channel (contact form, published email, or social message).

**Reason:** Converts a passive behavioral signal into a concrete introduction/lead rather than only internal analytics — central to the demonstrator's value story for NVIDIA.

**Status:** Decision-in-principle only; not implemented. Before any implementation, these must be resolved in a follow-up ADR:
- Consent/legitimacy basis for contacting an external, non-member entity that never opted into CIN.
- How to verify a discovered external contact channel genuinely belongs to the claimed company (anti-spoofing).
- Rate limiting per external entity so multiple users' signals don't trigger duplicate/repeated outreach.

No outbound-messaging capability is implemented in this release. This ADR records design intent and open questions only.

## ADR-009 — Investment Opportunity Explorer persistence and review gate

**Status:** Accepted for V1 implementation

**Decision:** `explore_investment_opportunities()` persists every newly discovered `POTENTIAL` result as an `Opportunity`, with `OpportunityProduct`, `OpportunityAssertion`, and a `ReasoningRun` trace. Repeated discovery for the same two products reuses the existing `Opportunity` record instead of creating a duplicate.

**Reason:** The Explorer is not a separate truth domain. Its result is an analytical hypothesis that must be traceable, auditable, reviewable, and later eligible for a human approval gate. Returning only transient dictionaries would break the chain into the investor-facing layer and would discard the durable provenance already modeled by `Opportunity`.

**Boundary:** Explorer persistence does **not** mean investor visibility. Newly created records remain `POTENTIAL` and are not exposed as investor-approved opportunities. A future investor endpoint must require an explicit human review approval record before returning an opportunity to an investor.

**Current review-contract note:** the existing review service currently uses the legacy decision vocabulary `ACCEPT / MODIFY / REJECT` and maps `ACCEPT` to `ACCEPTED`. Therefore this V1 does not silently rename that contract to `APPROVED`. Before the investor gateway is exposed, the review vocabulary and status transition must be migrated deliberately to one canonical approval contract (for example `APPROVED`) and covered by integration tests.

**Filter semantics:** query searches product name/category/description/goal and verified support-request goals. `activity_domain` and `support_type` constrain the candidate product set before pairing. Products must be `VERIFIED` and have verified evidence plus verified capability assertions.

## ADR-010 — Transactional outbox recovery

Redis delivery is best-effort after the PostgreSQL transaction commits. A Redis failure therefore does not turn a committed review into an HTTP 500. The transactional outbox remains `PENDING` and the periodic worker reconcile sweep re-enqueues stale events.

`PROCESSING` events carry `processing_started_at`; events older than `PROCESSING_TIMEOUT_SECONDS` are reset to `PENDING` and re-enqueued. Event claiming uses a row lock plus a status guard (`PENDING → PROCESSING`) so duplicate Redis deliveries do not execute the same event concurrently. Neo4j projection uses idempotent `MERGE` operations.

## ADR-011 — Logistics Capability Domain (C11)

- **Decision:** Add logistics as a first-class capability domain, not as a separate directory of transport providers.
- **Scope:** Products may declare logistics requirements (origin, destination, modes, storage, temperature, shelf life, packaging, customs, insurance, tracking, readiness). Logistics routes store transport mode, route characteristics, capacity, cold-chain/customs/tracking capabilities and verification status.
- **Evidence:** Logistics routes can be linked to existing Evidence records. Route/profile records remain `PENDING` until independently verified.
- **Opportunity integration:** Product opportunity discovery recognizes C11 complementarity with C01, C02, C03 and C10. The investment approval gate remains unchanged: logistics data can support a potential opportunity but does not itself approve or rank an investment.
- **Source of truth:** PostgreSQL remains authoritative. Neo4j projection and semantic matching can consume verified logistics facts in a later phase.
- **UI:** The homepage exposes a Logistics Intelligence entry point so local and international logistics can be explored without making it a separate silo.
## ADR-012 — Proactive Outreach (Signal-to-Lead)

**Decision:** CIN may convert a behavioral interest signal into a potential lead only after an explicit user opt-in action. The system uses a two-consent/verification gate: (1) the user explicitly requests that the company be informed of their interest, and (2) the external company's contact channel must be independently verified before any user identity is disclosed. Viewing content alone never starts outreach.

**Reason:** This turns a meaningful user signal into a concrete introduction while preserving user agency, company-channel authenticity, and auditable delivery controls. It extends ADR-008 without allowing passive tracking to become unsolicited outreach.

**Legitimacy / consent:** The initiating event is the authenticated user's explicit opt-in through the CIN signal endpoint. No outreach is triggered by a view, playback, impression, or other passive behavioral event. For an external non-member entity, no message is sent until its discovered public contact channel is verified through the existing Evidence verification model. Before verification, a digest may exist internally but cannot be delivered.

**Anti-spoofing:** Discovered contact channels are stored as ordinary Evidence with `evidence_kind=EXTERNAL_CONTACT_CHANNEL` and `validation_status=PENDING`. Verification uses the existing human-review/evidence pathway; no separate approval table or trust state is introduced. A channel remains unusable for delivery until its Evidence record is marked `VERIFIED`.

**Rate limiting / duplicate prevention:** A signal is idempotent on `(user_id, source_content_ref)`. Signals are aggregated per `external_entity_ref` into periodic digests rather than individual messages. Each entity has a configurable `cooldown_until`; reconciliation will not create a new digest while the entity remains inside its cooldown window.

**Identity protection:** No outbound delivery path exposes user identity while the contact channel is `PENDING` or `REJECTED`. Only the verified-delivery service constructs the identity-bearing delivery payload. There is no public API for an external entity to request or retrieve user identity.

**Delivery architecture:** PostgreSQL remains the source of truth. Digest reconciliation creates durable `PENDING` records; delivery is a separately callable service using an injectable sender interface. No real email, social-message, or external contact-form integration is implemented in this ADR.

**Status:** Implemented as a demonstrator workflow with an injectable sender. Real external delivery, production scheduler execution, and live infrastructure validation remain outside this release.



## ADR-013 — Institutional Intelligence Benchmarking

Accepted as a design research track. Public primary-source material from BlackRock, selected German asset managers and Artisan will be translated through `Source → Observed Practice → General Principle → CIN Adaptation → Candidate Module → Evidence`. The benchmark is not a ranking and does not imply proprietary internal knowledge.

## ADR-014 — Adaptive Choice-First Question Intelligence

Accepted as a planned product capability. CIN asks concise choice-first questions, always provides a free-answer/Other path, converts free text into traceable structured concepts, and chooses follow-up questions from information gaps. A single answer cannot silently modify production questions.

## ADR-015 — Autonomous AI Workforce & Agent Architecture

Accepted as a planned architecture. Specialized AI agents may operate above CIN's evidence and intelligence layers under explicit identity, permissions, tool/action allowlists, approval thresholds, rate limits and audit logging. External communication remains subject to ADR-012.

## ADR-016 — Institutional Client Intelligence Profiles

Accepted as a planned architecture. Client archetypes route vocabulary, questions, evidence needs, risk lenses, scenarios and reports. A client profile is a context/routing layer, not a score.
