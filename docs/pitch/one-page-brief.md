# Civilizational Intelligence Network (CIN) — One-Page Brief

**Product:** Evidence-first capability matching platform with governed outreach.

**Tagline:** Verified capabilities. Explainable opportunities. Consent-based introductions.

## The problem
Regional and industrial capabilities are fragmented, self-claimed, and hard to trust. Matching partners across value chains is slow and risky. Interest signals are either ignored or turned into spam.

## The solution
CIN models communities and companies as **Capability Nodes**. Every assertion requires evidence and independent human review before it becomes a verified fact. Verified facts are projected into a Knowledge Graph. Analytical engines then propose complementary opportunity paths — always as hypotheses for human review, never as automated decisions.

A separate, tightly controlled **Proactive Outreach** workflow converts an authenticated user’s explicit interest into a digest that is delivered only after the external party’s contact channel is verified.

## Core data rule
```
RAW DATA → EVIDENCE → HUMAN REVIEW → VERIFIED FACT → PostgreSQL (system of record)
       → Transactional Outbox → Redis → Neo4j Graph → Explainable Opportunity Paths
```

## Why it is trustworthy
- PostgreSQL is the single source of truth; Neo4j is a rebuildable projection.
- AI cannot promote unverified data to truth.
- Confidence measures evidence support only — never community ranking or success probability.
- Outreach requires two gates: (1) user explicit opt-in, (2) verified external contact channel.
- Full audit trail of reviews, assessments, and delivery decisions.

## Primary use cases
1. **Industrial & regional capability matching** for economic agencies and manufacturers.
2. **Governed signal-to-lead outreach** that never starts from passive views.

## Status
Technical demonstrator (v2.0, ADR-012). Architecture, domain model, and test suite are in place. Full production certification (live Docker runtime, load, TLS, backup/restore) remains on the production checklist.

## What we are not claiming
No civilizational ranking, no guaranteed commercial outcomes, no unmeasured GPU performance claims.
