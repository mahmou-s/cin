from apps.api.app.services.confidence import calculate_confidence, derive_independence_key


def evidence(score: float, key: str | None = None, **source):
    item = {
        "authority": score,
        "directness": score,
        "recency": score,
        "validation": score,
        "consistency": score,
        "independence": score,
        "completeness": score,
    }
    if key is not None:
        item["independence_key"] = key
    item.update(source)
    return item


def test_default_scored_evidence_does_not_create_high_confidence():
    score, level = calculate_confidence([
        evidence(.5, "source-a"),
        evidence(.5, "source-b"),
        evidence(.5, "source-c"),
    ])
    assert score == .849999
    assert level == "MEDIUM"


def test_many_weak_evidences_from_one_source_are_counted_once():
    score, level = calculate_confidence([
        evidence(.3, "same-source") for _ in range(10)
    ])
    assert score == .3
    assert level == "UNVERIFIED"


def test_high_requires_two_independent_groups():
    score, level = calculate_confidence([
        evidence(1.0, "source-a"),
        evidence(1.0, "source-b"),
    ])
    assert score == .9
    assert level == "HIGH"


def test_strong_strong_weak_stays_high():
    score, level = calculate_confidence([
        evidence(.8, "source-a"),
        evidence(.8, "source-b"),
        evidence(.2, "source-c"),
    ])
    assert score == .9
    assert level == "HIGH"


def test_high_score_is_gated_when_only_one_group_is_strong():
    score, level = calculate_confidence([
        evidence(1.0, "source-a"),
        evidence(.2, "source-b"),
        evidence(.2, "source-c"),
    ])
    assert score == .849999
    assert level == "MEDIUM"


def test_missing_source_identity_is_one_shared_unknown_group():
    score, level = calculate_confidence([
        evidence(1.0),
        evidence(1.0),
    ])
    assert score == .849999
    assert level == "MEDIUM"  # one unknown group cannot satisfy HIGH


def test_server_derives_source_group_from_url_host():
    assert derive_independence_key({"content_url": "https://example.org/report/123"}) == "derived-host:example.org"


def test_distinct_uploaded_files_without_url_share_one_unknown_group():
    evidences = [evidence(0.9, None, sha256=f"hash-{i}") for i in range(10)]
    score, level = calculate_confidence(evidences)
    assert score == 0.849999
    assert level == "MEDIUM"
    assert derive_independence_key({"sha256": "ABC123"}) == "__unknown_source__"
