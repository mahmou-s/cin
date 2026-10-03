# ADR-018 — Question Intelligence Alignment

## Status
Implemented — Wave 5.

## Decision
CIN's next-question engine must use the existing intelligence ecosystem, not question-language similarity alone. Question priority therefore incorporates:

- Client strategic objectives and constraints
- Capability context
- Evidence gaps around matched capability assertions
- Existing opportunity context
- Existing need/investment-request context
- Risk/resilience/continuity signals
- Information gain from unanswered questions

## Guardrails
- No claim is promoted to fact by question ranking.
- Evidence gaps are signals for clarification, not proof that a capability is weak.
- Opportunity and need matches are contextual signals, not investment recommendations.
- The ranking engine does not execute transactions or external actions.
- Every ranking result exposes reason codes and context references.

## Weighting
The Wave 5 intelligence-value score uses a deterministic weighted model:

- Base information value: 35%
- Capability context: 15%
- Evidence gap: 20%
- Opportunity context: 15%
- Need context: 5%
- Risk context: 10%

These weights are configuration candidates and should be validated against real user sessions before being treated as optimal.
