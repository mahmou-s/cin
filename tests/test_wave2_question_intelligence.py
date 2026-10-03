import asyncio
from apps.api.app.services.question_intelligence import concepts, DEFAULTS

def test_concepts_are_deterministic_and_bounded():
    out=concepts('We need a reliable investment partner and better liquidity planning')
    assert 'investment' in out
    assert 'partner' in out
    assert 'liquidity' in out
    assert len(out) <= 12

def test_institutional_segments_have_questions():
    assert DEFAULTS['ASSET_MANAGER']
    assert DEFAULTS['FAMILY_OFFICE']
    assert DEFAULTS['PENSION_FUND']
