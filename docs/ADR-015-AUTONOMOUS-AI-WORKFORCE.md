# ADR-015 — Autonomous AI Workforce & Agent Architecture

## Status
Accepted — planned implementation.

## Decision
CIN will support specialized AI employees/agents that execute governed workflows over CIN's evidence and intelligence layers. Artisan AI is used as a reference case for autonomous AI employee workflows; CIN does not copy or depend on Artisan.

## Agent levels
0 Observe
1 Recommend
2 Prepare
3 Human Approval
4 Guarded Autonomous
5 Autonomous Workflow

## Required controls
Every agent has:
- identity
- role
- permissions
- data-access scope
- tool allowlist
- action allowlist
- prohibited actions
- approval threshold
- rate limits
- audit log
- emergency stop

## Core flow
`CIN Intelligence → Agent Orchestrator → Agent → Tool → Outcome → Audit → Learning`.

## External communications
Existing ADR-012 consent and verified-channel requirements remain mandatory. Real external delivery is a separate integration and is not implied by this ADR.
