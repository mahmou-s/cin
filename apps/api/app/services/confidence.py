import math
from collections import defaultdict
from typing import Iterable
from urllib.parse import urlparse

from ..config import settings

WEIGHTS = {
    "authority": .20,
    "directness": .15,
    "recency": .10,
    "validation": .20,
    "consistency": .15,
    "independence": .10,
    "completeness": .10,
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value or 0.0)))


def _high_gate(independent_groups: int, strong_groups: int) -> bool:
    return (
        independent_groups >= settings.confidence_high_min_independent_groups
        and strong_groups >= settings.confidence_high_min_independent_groups
    )


def level(score: float, independent_groups: int = 0, strong_groups: int = 0) -> str:
    score = _clamp(score)
    if score >= settings.confidence_high_score_threshold and _high_gate(independent_groups, strong_groups):
        return "HIGH"
    if score >= .65:
        return "MEDIUM"
    if score >= .40:
        return "PRELIMINARY"
    return "UNVERIFIED"


def evidence_score(e: dict) -> float:
    return sum(weight * _clamp(e.get(key, 0)) for key, weight in WEIGHTS.items())


def derive_independence_key(e: dict) -> str:
    """Return a non-canonical derived key for reviewer visibility only.

    Submitter-derived host/hash values can never establish independence.
    Canonical grouping remains __unknown_source__ until a reviewer confirms
    or explicitly supplies independence_key.
    """
    url = e.get("content_url")
    if url:
        host = (urlparse(str(url)).hostname or "").strip().lower()
        if host:
            return f"derived-host:{host}"

    sha256 = e.get("sha256")
    # A file hash identifies duplicate content, not an independent publisher.
    # Without a reviewer source key or URL host, all such evidence shares one
    # unknown group. Identical hashes therefore remain duplicates in that group.
    return "__unknown_source__"


def independence_key(e: dict) -> str:
    """Return the canonical/explicit grouping key for already-reviewed data."""
    key = e.get("independence_key")
    if key:
        return str(key).strip()
    return derive_independence_key(e)


def strongest_by_group(evidences: Iterable[dict]) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for evidence in evidences:
        grouped[independence_key(evidence)].append(evidence_score(evidence))
    return {key: max(scores) for key, scores in grouped.items()}


def combined_support(scores: list[float]) -> float:
    """Bounded noisy-OR over independent source groups."""
    value = 1.0
    for score in scores:
        value *= 1 - _clamp(score)
    return min(settings.confidence_combined_support_cap, 1 - value)


def calculate_confidence_details(
    evidences: list[dict],
    contradiction_score: float = 0.0,
) -> tuple[float, str, float, dict]:
    grouped = strongest_by_group(evidences)
    support = combined_support(list(grouped.values())) if grouped else 0.0
    raw_score = max(0.0, min(1.0, support * (1 - _clamp(contradiction_score))))
    strong_groups = sum(
        1 for value in grouped.values()
        if value >= settings.confidence_high_min_group_score
    )

    # Keep the persisted numeric score consistent with the HIGH gate. Without
    # this, a 0.875 score could be consumed downstream as if it were HIGH even
    # when only one independent group was strong enough.
    if raw_score >= settings.confidence_high_score_threshold and not _high_gate(len(grouped), strong_groups):
        score = min(raw_score, settings.confidence_high_score_threshold - settings.confidence_high_gate_epsilon)
    else:
        score = raw_score

    score = round(score, 6)
    reasons = {
        "independent_groups": len(grouped),
        "strong_groups": strong_groups,
        "minimum_independent_groups": settings.confidence_high_min_independent_groups,
        "minimum_group_score": settings.confidence_high_min_group_score,
        "high_score_threshold": settings.confidence_high_score_threshold,
        "high_gate_satisfied": _high_gate(len(grouped), strong_groups),
        "score_gated": score != round(raw_score, 6),
    }
    return score, level(score, len(grouped), strong_groups), raw_score, reasons


def calculate_confidence(evidences: list[dict], contradiction_score: float = 0.0) -> tuple[float, str]:
    score, level_name, _, _ = calculate_confidence_details(evidences, contradiction_score)
    return score, level_name


def recency_from_age(age_days: float, tau: float = 365.0) -> float:
    if age_days < 0:
        return 1.0
    return math.exp(-age_days / tau)
