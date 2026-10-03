# Wave 5 — Question Intelligence Alignment Implementation Report

## Objective
Connect the Wave 4 Question Knowledge Graph to CIN's existing Capability, Evidence, Opportunity, Need and Risk-related context so the next question is selected by potential intelligence value.

## Implemented
- `CINQuestionIntelligenceSignal` persistence model.
- Alembic migration `0016_question_intelligence_alignment`.
- Deterministic alignment service: `question_alignment.py`.
- Enhanced session progression after each answer.
- Enhanced ranking endpoint with component signals and context references.
- ADR-018 documenting the decision and guardrails.
- Wave 5 unit tests.

## Data Flow
`Answer -> Concepts -> Question Knowledge -> Client Context -> Capability Context -> Evidence Gap -> Opportunity/Need Context -> Risk Context -> Intelligence Value -> Next Question`

## Important distinction
The engine identifies information gaps and contextual matches. It does not infer that an opportunity, risk, or capability is true merely because a question matched it.

## Verification
The full test suite must be run after packaging. Web build is environment-dependent when Node dependencies are absent.
