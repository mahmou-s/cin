# CIN Wave 4 — Question Knowledge Graph + Evidence-Aware Prioritization

## Implemented
- Question Knowledge Graph projection: question -> concept links.
- Evidence-state field for each question concept (`UNKNOWN`, `VALIDATED` as applicable).
- Deterministic, auditable question prioritization using client objectives, constraints, repeated patterns, validated patterns, novelty/information-gain, and base priority.
- Priority signal audit records with component scores and reason codes.
- Session ranking endpoint for explainable next-question ordering.
- Reviewer-only knowledge graph endpoint.
- Existing Wave 3 governance remains authoritative: learned questions stay `CANDIDATE` until human approval.

## Decision rule
The prioritizer is decision support, not an autonomous truth engine. It does not infer factual evidence from a question. `evidence_signal` is only increased by validated patterns; unknown evidence remains explicit.

## API
- `GET /api/v1/questions/sessions/{session_id}/ranking`
- `GET /api/v1/questions/knowledge` (reviewer)

## Migration
`0015_wave4_question_knowledge_graph`

## Scoring
`0.30 objective + 0.20 constraint + 0.20 pattern + 0.20 evidence + 0.10 novelty`, plus a small configurable base-priority tie-break component.

## Next
Wave 5 should connect these question concepts to actual Capability / Need / Evidence / Risk / Opportunity entities rather than relying only on language-derived concepts.
