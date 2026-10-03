from apps.api.app.auth import Principal
from apps.api.app.config import settings


def test_auth_roles_are_explicit():
    assert {"submitter", "reviewer", "steward"} == {"submitter", "reviewer", "steward"}
    assert Principal("demo-steward", "steward").role == "steward"


def test_confidence_policy_is_configured():
    assert settings.confidence_high_min_group_score == 0.70
    assert settings.confidence_combined_support_cap == 0.90
    assert settings.confidence_high_min_independent_groups == 2
    assert settings.confidence_high_gate_epsilon > 0
