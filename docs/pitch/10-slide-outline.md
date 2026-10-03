# CIN — 10-Slide Outline (Commercial Version)

1. **Problem**  
   Verified industrial and regional capabilities are fragmented. Self-reported data is untrusted. Matching is slow and risky. Interest signals become spam.

2. **Solution**  
   Evidence-first capability matching platform. Every claim needs evidence + human review. Complementary opportunity paths are generated only from verified facts. Outreach is consent-gated.

3. **Data model**  
   Capability Nodes · Evidence · Confidence (evidence support only) · Value Chain links · Outreach signals & digests.

4. **Trust pipeline**  
   Input → Evidence → Validation → Human Review → Verified Fact → PostgreSQL → Outbox → Graph → Human-reviewed Opportunities.

5. **Knowledge Graph**  
   Relations without ranking communities. Rebuildable Neo4j projection. Explainable paths.

6. **Two flagship use cases**  
   (A) Industrial / regional capability matching for agencies and manufacturers.  
   (B) Governed proactive outreach (explicit signal → verified channel → digest).

7. **Demo narrative**  
   Seed verified capabilities → discover complementary path → human review of opportunity → explicit interest signal → channel verification → controlled delivery.

8. **Governance & privacy**  
   Authenticated roles, independent review, source-group confirmation, audit events, no passive-view outreach, identity protected until channel is verified.

9. **Reliability architecture**  
   PostgreSQL system of record · Transactional outbox · Redis delivery · Idempotent worker · Neo4j projection · Alembic migrations.

10. **Roadmap & ask**  
    Full staging runtime verification → one focused geography/vertical pilot → measure verified nodes + accepted opportunity paths + successful governed deliveries. Optional later: GPU-accelerated extraction/embeddings under measured conditions.
