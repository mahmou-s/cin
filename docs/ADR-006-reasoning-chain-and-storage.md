# ADR-006 — Shared capability chains and reasoning data source

**Status:** Accepted

All civilizational opportunity and path-reasoning engines use the shared
`apps/api/app/services/chain_definitions.py` module. It is the single source of
truth for chain definitions, labels, transitions, and the demo chain
`C01 → C10 → C06 → C02`.

Support aggregation is documented and consistent:

- **weakest-link:** minimum verified assertion confidence in the chain; exposed
  as the conservative `support_score`.
- **average:** arithmetic mean of the same assertion confidence values; exposed
  as descriptive `support_average`.

Neither value is a probability, ranking, or judgment of a community.

Reasoning currently reads verified capability assertions from **PostgreSQL**.
Neo4j is currently the projection and visualization layer. Neo4j traversal is
intentionally deferred; no claim is made that the current reasoning engine is
performing graph-native traversal.
