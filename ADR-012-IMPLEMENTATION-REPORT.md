# ADR-012 Implementation Report — Proactive Outreach (Signal-to-Lead)

## Scope
Implemented ADR-012 on top of CIN Value Chain V1. No automatic outreach is triggered by content viewing. The only entry point is the authenticated explicit-interest endpoint.

## Implemented
- `apps/api/migrations/versions/0012_proactive_outreach.py`
  - migration head: `0012_proactive_outreach`
  - `users` identity table keyed by authenticated `principal_id`
  - `outreach_signals` with unique `(user_id, source_content_ref)`
  - `outreach_digests`
  - normalized `outreach_digest_signals` link table
  - `Evidence.evidence_kind=EXTERNAL_CONTACT_CHANNEL`
  - `Evidence.external_entity_ref`
- `apps/api/app/services/outreach.py`
  - idempotent signal recording
  - injectable contact-channel discovery
  - per-entity digest reconciliation and cooldown
  - verified-channel-only delivery with injectable sender
- `apps/api/app/api/v1/outreach.py`
  - authenticated `POST /api/v1/outreach/signal`
  - no endpoint exposes user identity to an external entity
- `apps/api/app/models.py`, `schemas.py`, `config.py`, `main.py`
- `tests/test_proactive_outreach.py`
  - idempotency
  - cooldown
  - pending-channel no-send
  - verified-channel send and SENT transition
  - full signal → digest → verify → deliver flow
- `docs/ARCHITECTURE_DECISIONS.md`
  - ADR-008 marked `Superseded by ADR-012`
  - ADR-012 added
- `CHANGELOG.md`
  - implementation status and environment limitations recorded

## Verification actually run
- Python compilation: `PYTHON_COMPILE_OK`
- Alembic static head check: `0012_proactive_outreach (head)`
- Full pytest: `68 passed, 7 skipped in 0.71s`

### Skips
- `tests/test_integration_behavior.py`: `fakeredis` is not installed.
- 5 tests in `tests/test_proactive_outreach.py`: PostgreSQL unavailable because `asyncpg` is not installed.
- 1 test in `tests/test_review_validation.py`: `asyncpg` is not installed.

No test failed.

## Not executed / not verified in this environment
- Real PostgreSQL migration execution.
- Real Redis execution / outbox worker scheduling.
- Real Docker Compose runtime.
- Real external email, contact-form, social-message, or other outbound delivery.
- Production scheduler execution.

The sender is deliberately an injectable interface/stub; no external messaging integration was added.
