# ADR-017 — Question Knowledge Graph and Evidence-Aware Prioritization

## Context
CIN needs to ask the smallest number of questions that produce the highest information value while remaining auditable.

## Decision
Represent questions as knowledge-graph projections over concepts, and rank unanswered questions per client profile using explainable signals. Keep factual evidence separate from inferred concepts. A question cannot become active solely because its concept appears frequently; Wave 3 human governance remains mandatory.

## Consequences
- Better adaptive conversations.
- Explainable next-question selection.
- Persistent audit trail for prioritization.
- Future-ready integration with Capability, Need, Evidence, Risk and Opportunity nodes.
- No claim that language-derived concepts are verified facts.
