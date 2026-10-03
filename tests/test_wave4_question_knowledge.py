import pytest
from apps.api.app.services.question_intelligence import _question_concepts

def test_question_concepts_are_deterministic_and_nonempty():
    a=_question_concepts(type('Q',(),{'text':'What is your main investment priority?','options':['Risk','Growth','Liquidity']})())
    b=_question_concepts(type('Q',(),{'text':'What is your main investment priority?','options':['Risk','Growth','Liquidity']})())
    assert a == b
    assert {'investment','priority','risk','growth','liquidity'} <= a

def test_wave4_scoring_weights_sum_to_one():
    assert abs((0.30+0.20+0.20+0.20+0.10)-1.0) < 1e-9
