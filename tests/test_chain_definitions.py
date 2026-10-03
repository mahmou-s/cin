from apps.api.app.services.chain_definitions import CHAIN_DEFINITIONS, PATH_LABELS, PATH_TRANSITIONS, aggregate_support


def test_demo_chain_is_shared_by_both_reasoning_engines():
    chain = ("C01", "C10", "C06", "C02")
    assert chain in CHAIN_DEFINITIONS
    assert PATH_LABELS[chain]
    assert "C10" in PATH_TRANSITIONS["C01"]
    assert "C06" in PATH_TRANSITIONS["C10"]
    assert "C02" in PATH_TRANSITIONS["C06"]


def test_support_reports_weakest_link_and_average():
    assert aggregate_support([0.9, 0.8, 0.7]) == {"weakest_link": 0.7, "average": 0.8}
