# Wave 6 — Future Intelligence + Scenario-Aware Questioning

## Objective
Extend CIN questioning from present-state discovery to future-oriented intelligence without making unsupported predictions.

## Implemented
- Future vision, planning horizon, preferred scenarios and readiness barriers on Client Intelligence Profile.
- Future-oriented questions for every client segment.
- Deterministic Future Intelligence ranking service.
- Scenario relevance, readiness gap, future opportunity and uncertainty-reduction signals.
- Future ranking endpoint: `/api/v1/questions/sessions/{session_id}/future-ranking`.
- Persistence model `CINFutureIntelligenceSignal`.
- Alembic migration `0017_wave6_future_intelligence`.
- Wave 6 tests.

## Guardrails
CIN does not predict which scenario will occur. Scenario labels represent user-selected planning contexts or analytical frames. A readiness gap is an information signal, not a verified deficiency until supported by evidence.

## Data Flow
`Future Vision -> Scenario Context -> Readiness Gap -> Opportunity Context -> Question Ranking -> Evidence Collection -> Future Readiness`
