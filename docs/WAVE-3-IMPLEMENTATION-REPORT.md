# Wave 3 — Question Learning & Governance

## Objective
Convert repeated user answers into governed question candidates without allowing a single answer to mutate production questioning.

## Implemented
- Repeated-pattern threshold: at least 3 occurrences and at least 2 distinct sessions.
- Candidate generation from recurring concepts.
- Candidate questions are created with `CANDIDATE` status only.
- Reviewer endpoints list and approve/reject candidates.
- Approval activates the question and marks its source pattern validated.
- Rejection retires the candidate.
- Pattern records track distinct session count and candidate generation timestamp.
- Question records track reviewer, review time and review note.

## Safety invariant
A user answer can create a signal. Repetition creates a pattern. Validation creates a production question. No automatic activation occurs from raw user input.

## Next integration
Wave 4 should connect approved question candidates to the Question Knowledge Graph and client-segment routing, then add evidence-aware question prioritization.
