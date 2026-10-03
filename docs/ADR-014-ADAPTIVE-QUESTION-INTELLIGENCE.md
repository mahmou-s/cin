# ADR-014 — Adaptive Choice-First Question Intelligence

## Status
Accepted — planned implementation.

## Decision
CIN will collect high-value information through short choice-first questions with a mandatory free-answer escape path.

## Interaction
`Ask → Choose → Other/Free Answer → Understand → Identify Information Gap → Ask Follow-up`.

## Requirements
- Options are structured and concise.
- "Other" never forces an inaccurate answer.
- Free text is parsed into structured concepts but remains traceable to the raw answer.
- Follow-up questions are selected from information gaps.
- Production question changes require governed validation.
- A single answer cannot change production behavior.

## Learning contract
`Signal → Pattern → Candidate → Validation → Approved Question`.

## Safety
No personal or sensitive inference may be generated merely because an option exists. The system must distinguish user-provided facts from model interpretation.
