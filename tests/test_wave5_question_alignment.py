import pytest
from apps.api.app.services.question_alignment import overlap, tokens

def test_overlap_is_bounded_and_deterministic():
    assert overlap({'growth','risk'},{'growth'}) == pytest.approx(1/3)
    assert overlap(set(), {'growth'}) == 0.0
    assert overlap({'growth','risk','capital'},{'growth','risk','capital','liquidity'}) == 1.0

def test_tokens_filters_common_words():
    assert 'organization' not in tokens('What is the main organization priority?')
    assert 'priority' in tokens('What is the main organization priority?')
