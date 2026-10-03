# CIN 1 — Master Update & Development Plan
## Unified roadmap derived from the CIN Round 4 baseline and the October 2026 design decisions

### Status
- Baseline package: `CIN-v2.0-FIXED-E2E-READY-ROUND4(1).zip`
- Baseline migration head: `0012_proactive_outreach`
- This document is the controlling roadmap for the next CIN evolution.
- New capabilities in this roadmap are **planned unless explicitly marked implemented**.

## 1. Baseline assessment

The Round 4 package already establishes:
- PostgreSQL as System of Record.
- Transactional outbox as integration boundary.
- Redis as delivery layer.
- Neo4j as rebuildable graph projection.
- Evidence + human-review gating.
- Evidence-based confidence with independence rules.
- Opportunity-as-hypothesis semantics.
- Product / capability / evidence opportunity discovery.
- Value-chain and logistics domains.
- Consent-gated proactive outreach.
- CPU-first / GPU-ready positioning without unsupported NVIDIA performance claims.

The baseline also records that full PostgreSQL/Redis/Neo4j/Docker/Next.js runtime verification remains outstanding.

## 2. New strategic design tracks

### Track A — Institutional Intelligence Benchmarking
Study public, primary-source material from:
1. BlackRock
2. DWS
3. Union Investment
4. Deka Investment
5. Later: Allianz Global Investors, Flossbach von Storch, Metzler, Helaba Invest, HANSAINVEST, Ampega and other relevant institutions.

The objective is not to rank firms. It is to extract reusable design principles:
- Client segmentation
- Data architecture
- Common data language
- Whole-portfolio / whole-system views
- Risk and scenario analysis
- Research workflows
- Decision support
- Governance and stewardship
- AI operating models
- Institutional reporting
- Long-term client relationship design
- Product/platform evolution

Each lesson must be recorded as:
`Source → Observed Practice → General Principle → CIN Adaptation → Candidate Module → Evidence/Reference`.

### Track B — Institutional Client Intelligence
Introduce a Client Intelligence Profile and client-type adaptive workflows.

Initial client archetypes:
- Asset Manager
- Pension Fund
- Insurance
- Bank
- Family Office
- Corporation
- Government / Official Institution
- Foundation
- Healthcare Institution
- University
- SME
- Family Business
- Community / Regional Development Organization

The profile controls vocabulary, question priorities, evidence needs, risk lenses, scenario templates and executive reporting.

### Track C — Adaptive Human Intelligence
Evolve Choice-First Question Engine into Adaptive Choice-First Intelligence.

Interaction loop:
`Ask → Choose → Free Answer if needed → Understand → Learn → Adapt → Ask Again`.

Requirements:
- Short, easy questions with high information value.
- Structured options by default.
- Always provide an "Other / Write your own answer" path.
- Do not force a user into an inaccurate option.
- Free-text answers are parsed into concepts, intent, capability, need, constraint, risk, opportunity and information gaps.
- Follow-up questions are selected from the resulting information gaps.

### Track D — Question Learning Engine
New user answers may generate candidate options/questions for later users.

Learning policy:
`Single Answer = Signal`
`Repeated Pattern = Candidate Pattern`
`Validated Pattern = Candidate Question`
`Governed Approval = Production Question`

No single user answer may silently alter production questions.

The engine must retain:
- source pattern
- frequency
- client types
- sectors
- geography where appropriate
- confidence
- review status
- first/last observed dates
- reason for question creation
- lineage to the originating answers

### Track E — Risk / Scenario / Future Intelligence
Extend existing reasoning with:
- Risk & Resilience Intelligence
- Scenario Intelligence
- Future Readiness
- Future Imagination / Future Inspiration
- Capability Gap analysis
- Dependency and concentration analysis

Scenario families:
- Current Path
- Growth
- Stress
- Opportunity
- Transformation

Outputs must separate:
`Known / Inferred / Uncertain / Missing Information`.

### Track F — Autonomous AI Workforce
Study Artisan AI as an autonomous-AI-employee reference architecture, not as a component to copy blindly.

Candidate CIN AI employees:
- Research Agent
- Opportunity Agent
- Investor Relations Agent
- Business Development Agent
- Partnership Agent
- Follow-up Agent
- Meeting Agent
- Report Agent
- Family Continuity Agent
- Community Development Agent

Agent execution levels:
0 Observe
1 Recommend
2 Prepare
3 Human Approval
4 Guarded Autonomous
5 Autonomous Workflow

Every agent requires:
- identity
- role
- permissions
- data access scope
- tools
- allowed actions
- prohibited actions
- approval threshold
- rate limits
- audit trail
- kill switch

### Track G — AI Workforce Orchestration
Target flow:
`CIN Intelligence Core → Agent Orchestrator → Specialized Agents → External Tools/CRM/Email/Calendar → Outcome → Audit → Learning`.

Agents must operate on governed CIN evidence and policies. They are not independent sources of truth.

Potential integrations:
- Salesforce
- HubSpot
- Google Workspace
- Microsoft 365
- Calendar systems
- Email
- approved research/data providers

Integration architecture must preserve PostgreSQL as the system of record and use explicit consent/authorization boundaries.

### Track H — Reputation, Privacy and Agent Safety
For external communication:
- domain reputation controls
- rate limits
- suppression / opt-out handling
- duplicate prevention
- approval gates
- content policies
- identity protection
- data minimization
- audit logs
- emergency stop
- verified destination/contact channel
- campaign-level controls

The existing ADR-012 consent + verified-channel gate remains the minimum standard.

## 3. Executive Intelligence Language

CIN should behave like a strategic intelligence conversation rather than a generic survey.

Preferred sequence:
1. Objective
2. Priority
3. Constraint
4. Capability
5. Evidence
6. Risk
7. Opportunity
8. Readiness
9. Decision required
10. Next action

Principle:
**Maximum useful intelligence from minimum questions.**

## 4. Executive report target

The future institutional report should contain:
1. Executive Summary
2. Strategic Objectives
3. Current Capabilities
4. Capability Gaps
5. Evidence Quality
6. Opportunities
7. Risks
8. Scenarios
9. Network / Partners
10. Capital / Resource Requirements
11. Future Readiness
12. Unknowns / Data Gaps
13. Questions Requiring Clarification
14. Next Actions
15. Audit / Evidence Appendix

## 5. Institutional lessons architecture

CIN will maintain an institutional benchmark knowledge base.

Example:
`BlackRock → Aladdin / risk / workflow → common design principle → CIN module`
`DWS → institutional solutions / asset management → client-adaptive principle → CIN module`
`Union Investment → customized institutional mandates → client-intelligence principle → CIN module`
`Deka → multi-asset / institutional solutions → allocation/workflow principle → CIN module`
`Artisan → AI employees / autonomous workflows → agent architecture principle → CIN module`

No firm is used as a political, quality or performance ranking. The benchmark is for design learning only.

## 6. Implementation order

### Wave 1 — Baseline and research
- Audit Round 4.
- Freeze baseline.
- Create source registry.
- Build BlackRock study.
- Build German asset-management study.
- Build Artisan study.
- Map lessons to CIN.

### Wave 2 — Human Intelligence
- Client Intelligence Profile.
- Executive Intelligence Language.
- Adaptive Choice-First engine.
- Free Answer / Other path.
- Information-gap follow-up selection.

### Wave 3 — Learning
- Answer understanding.
- Pattern discovery.
- Question candidate generation.
- Question governance.
- Question knowledge graph.

### Wave 4 — Intelligence
- Risk & Resilience.
- Scenario Intelligence.
- Future Intelligence.
- Capability Gap analysis.

### Wave 5 — Autonomous Workforce
- Agent registry.
- Permission model.
- Agent orchestrator.
- Research Agent.
- Opportunity Agent.
- Business Development Agent.
- Meeting Agent.
- Reporting Agent.
- Audit / kill switch.

### Wave 6 — Institutional Product
- Investment intelligence.
- Institutional opportunity explorer.
- Executive reports.
- CRM / email / calendar connectors.
- Controlled pilot.

### Wave 7 — Validation
- Unit tests.
- Integration tests.
- Full Docker runtime.
- PostgreSQL migration round trip.
- Redis delivery.
- Neo4j projection.
- Next.js production build.
- Security testing.
- Load/resource testing.
- Backup/restore.
- Agent safety tests.
- Human approval / consent tests.

## 7. Non-negotiable architecture rules

1. PostgreSQL remains the authoritative source of truth.
2. Neo4j remains rebuildable projection.
3. Evidence and human review gate canonical facts.
4. AI inference is not evidence.
5. Opportunity remains a hypothesis until explicitly approved.
6. Confidence is evidence support, not a capability or community score.
7. AI agents cannot silently change canonical truth.
8. Production questions cannot change from a single user response.
9. External communication requires explicit authorization and appropriate verified destination controls.
10. No unsupported GPU/NVIDIA performance claims.
11. Every externally sourced design lesson retains provenance.
12. `Known / Inferred / Uncertain / Missing` must remain distinguishable.

## 8. Definition of done for this roadmap

CIN is ready for the next institutional pilot when:
- baseline runtime is fully verified;
- client-type adaptive questioning works;
- free-text answers are safely interpreted;
- question learning is governed and auditable;
- evidence provenance is preserved;
- risk/scenario outputs distinguish facts from inference;
- AI agents operate under explicit permissions and approval gates;
- CRM/calendar/email integrations are tested;
- executive reporting is repeatable;
- security, privacy and domain-reputation controls are tested.


## Wave 4 — Completed
Question Knowledge Graph + Evidence-Aware Question Prioritization.
The implementation ranks unanswered questions from client objectives, constraints, repeated patterns, validated patterns and novelty, while preserving explicit evidence-state and Wave 3 human governance.

## Wave 5 Status — Implemented
Question Intelligence Alignment now connects the adaptive question layer to existing Capability, Evidence, Opportunity and Need context, with risk/resilience proxy signals. Ranking remains deterministic, explainable and non-decisional. Migration: `0016_question_intelligence_alignment`.

### Wave 5 acceptance criteria
- [x] Capability context signal
- [x] Evidence-gap signal
- [x] Opportunity context signal
- [x] Need context signal
- [x] Risk/context signal
- [x] Explainable reason codes
- [x] Persisted intelligence signals
- [x] Session next-question integration
- [x] Full Python test suite passing
