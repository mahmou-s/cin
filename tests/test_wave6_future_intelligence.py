import pytest
from apps.api.app.services.future_intelligence import overlap, tokens

def test_future_overlap_bounded():
    assert overlap({'growth','future'},{'growth'}) == pytest.approx(1/3)
    assert overlap(set(), {'future'}) == 0.0
    assert overlap({'future','scenario','readiness','risk'},{'future','scenario','readiness','risk'}) == 1.0

def test_future_tokens_keep_meaningful_terms():
    t=tokens('What future outcome would your organization achieve through transformation?')
    assert 'future' in t
    assert 'transformation' in t
    assert 'what' not in t
