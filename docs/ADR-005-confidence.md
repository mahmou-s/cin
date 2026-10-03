# ADR-005 — Confidence gating and source independence

**Status:** Accepted

Evidence is grouped by independent source, not by file count. A reviewer-supplied
`independence_key` is authoritative. If absent, the server derives a group from
the URL host. If there is no URL host, all such evidence shares one
`__unknown_source__` group. SHA-256 identifies duplicate content and is not used
as a publisher-independence key.

Configuration values:

- `CONFIDENCE_HIGH_MIN_GROUP_SCORE=0.70`
- `CONFIDENCE_COMBINED_SUPPORT_CAP=0.90`
- `CONFIDENCE_HIGH_SCORE_THRESHOLD=0.85`
- `CONFIDENCE_HIGH_MIN_INDEPENDENT_GROUPS=2`
- `CONFIDENCE_HIGH_GATE_EPSILON=0.000001`

HIGH requires at least two independent groups and at least two groups whose
individual evidence score is at least 0.70. The raw/ungated score and gate
reasons are persisted for audit, while the canonical score is gated before it
can be consumed by downstream reasoning. The score is an evidence-support
policy metric, not a probability.
