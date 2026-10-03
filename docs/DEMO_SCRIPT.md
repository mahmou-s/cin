# CIN NVIDIA Demonstration Script

## 1. Start

Show the architecture:

`Submission → Evidence → Validation → Human Review → Outbox → Redis → Neo4j → Reasoning`

State that PostgreSQL is the source of truth and Neo4j is a rebuildable projection.

## 2. Submit evidence

Open the Submission Form and submit one capability assertion with evidence.

Expected state:

`SUBMITTED`

## 3. Review

Open the review queue and verify the assertion.

Expected transition:

`SUBMITTED → VERIFIED`

## 4. Observe asynchronous projection

Show the outbox event and Redis queue flow. The Worker consumes the event and writes the verified capability into Neo4j.

## 5. Show graph

Open the graph visualization and select the community, assertion and capability nodes.

## 6. Show reasoning

Run opportunity discovery and display the capability chain.

## 7. Show trust boundary

Explain that the system never treats an LLM proposal as a verified fact.

## 8. NVIDIA discussion

Move from the deterministic demonstrator to the acceleration roadmap:

- evidence understanding;
- embeddings;
- graph learning;
- scenario search;
- grounded AI reasoning.

Do not present future acceleration as an existing benchmark.
