from apps.api.app.services.question_intelligence import candidate_question_text, QUESTION_LEARNING_MIN_OCCURRENCES, QUESTION_LEARNING_MIN_SESSIONS

def test_wave3_governance_thresholds_are_conservative():
    assert QUESTION_LEARNING_MIN_OCCURRENCES >= 3
    assert QUESTION_LEARNING_MIN_SESSIONS >= 2

def test_candidate_question_is_human_readable_and_has_other_path():
    text, options = candidate_question_text('investment_partner', 'ASSET_MANAGER')
    assert 'investment partner' in text
    assert 'Other' in options
    assert len(options) <= 6
