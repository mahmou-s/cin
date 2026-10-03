# CIN Product Focus — Commercial Positioning (v2.0+)

## One-sentence product definition

**CIN is an evidence-first capability matching platform that turns verified community and company capabilities into explainable complementary opportunity paths — with governed, consent-based outreach.**

## Primary commercial use cases (narrowed)

### Use Case 1 — Industrial & Regional Capability Matching
**Buyer:** Economic development agencies, industrial parks, export promotion bodies, large manufacturers seeking local/regional partners.

**Problem:** Capabilities of SMEs, regions, and communities are fragmented, self-claimed, and hard to trust. Matching is slow, manual, and prone to over-claiming.

**CIN value:**
- Capability assertions must be backed by evidence and human review.
- Confidence measures evidence support only (never a ranking of communities).
- Knowledge Graph surfaces complementary paths (e.g. “Region A has verified machining + Region B has verified logistics → potential value-chain link”).
- Value Chain model supports Component → Manufacturer → Exporter → … → Service Provider.

**Success metric:** Number of verified capability nodes + number of human-reviewed opportunity paths accepted by operators.

### Use Case 2 — Governed Proactive Outreach (Signal-to-Lead)
**Buyer:** Platforms, marketplaces, or agencies that want to introduce interested parties without spam or privacy violations.

**Problem:** Passive interest signals are either ignored or turned into unsolicited outreach that damages trust.

**CIN value (ADR-012):**
- Outreach starts only from an authenticated user’s explicit opt-in signal.
- External contact channels must be independently verified as Evidence before any identity is disclosed.
- Digests + cooldown prevent message flooding.
- Full audit trail in PostgreSQL.

**Success metric:** Signals recorded → digests created → verified-channel deliveries completed, with zero passive-view triggers.

### Secondary / future use cases (not primary in this release)
- Investment opportunity exploration (existing explorer is hypothesis-only).
- Logistics corridor intelligence.
- Cross-border industrial symbiosis / waste-to-resource matching (research adjacent).

## What CIN deliberately does NOT claim
- It does not rank communities or produce a “civilizational score”.
- It does not guarantee commercial willingness, financing, or legal feasibility.
- Opportunity paths are hypotheses requiring human review.
- No production performance or NVIDIA GPU claims are made until measured.

## Positioning statement (for investors / partners)

> Most supplier-discovery and capability platforms either (a) trust self-reported data or (b) use black-box AI rankings. CIN is different: every capability fact must pass evidence + human review before it enters the graph, and every outreach action requires explicit user consent plus verified contact channels. The result is a trustworthy matching layer that economic agencies and industrial networks can actually rely on.

## Recommended next product steps
1. Pick one geography + one vertical (e.g. light manufacturing in a specific region) and seed real verified data.
2. Run full docker-compose + end-to-end demo with real PostgreSQL, Redis, Neo4j.
3. Instrument the two success metrics above.
4. Keep the civilizational theory as background intellectual property; lead all external communication with Use Case 1 and Use Case 2.
