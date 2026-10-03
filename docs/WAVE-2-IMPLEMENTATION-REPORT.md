# CIN Wave 2 — Client Intelligence + Adaptive Choice-First Question Engine

## Implemented
- Client Intelligence Profile API with institution/client segments.
- Adaptive Choice-First question sessions.
- Choice answers and explicit `OTHER`/free-text escape path.
- Concept extraction from free text (deterministic baseline; no LLM dependency).
- Question usage tracking and pattern accumulation.
- Pattern governance endpoint for reviewer inspection.
- Segment-aware seed questions for institutional clients.
- Web UI component for starting a session and answering by choice or free text.

## Data flow
`Client Segment → Question → Choice/Free Text → Concept Extraction → Pattern Store → Next Question`

## Governance rule
A new answer is a signal. Repeated concepts become patterns. Promotion to a production question requires validation; Wave 2 does not auto-promote a single user answer into a new production question.

## Verification
- Python compile: PASS
- Existing profile/production tests: 9 PASS
- Web build: NOT RUN because the provided workspace has no installed `node_modules` / `next` executable. The source component is included and requires the normal dependency install before browser build verification.
