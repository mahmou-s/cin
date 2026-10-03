from types import SimpleNamespace
from uuid import uuid4

from apps.api.app.services.product_opportunity_discovery import _candidate
from apps.api.app.models import Base, ProductCapabilityAssertion, OpportunityProduct


def _evidence():
    return SimpleNamespace(id=uuid4(), validation_status="VERIFIED")


def _assertion(code, evidence):
    return SimpleNamespace(
        id=uuid4(), status="VERIFIED", confidence_score=0.8,
        capability_type=SimpleNamespace(code=code, name=code), evidences=[evidence],
    )


def _product(profile_id, name, code):
    evidence = _evidence()
    return SimpleNamespace(
        id=uuid4(), profile_id=profile_id, name=name,
        evidences=[evidence], capability_assertions=[_assertion(code, evidence)],
        ai_confidence_score=0.75,
    )


def test_product_discovery_requires_verified_evidence_and_complementary_capabilities():
    a = _product(uuid4(), "Tomato", "C01")
    b = _product(uuid4(), "Export Network", "C03")
    candidate = _candidate(a, b)
    assert candidate is not None
    assert candidate["capability_codes"] == ["C01", "C03"]
    assert len(candidate["evidence_ids"]) >= 2
    assert candidate["confidence_floor"] == 0.75


def test_product_discovery_rejects_missing_verified_evidence():
    a = _product(uuid4(), "Tomato", "C01")
    b = _product(uuid4(), "Export Network", "C03")
    b.evidences[0].validation_status = "PENDING"
    assert _candidate(a, b) is None


def test_product_opportunity_join_tables_are_real_orm_models():
    assert ProductCapabilityAssertion.__tablename__ == "product_capability_assertions"
    assert OpportunityProduct.__tablename__ == "opportunity_products"
    assert "product_capability_assertions" in Base.metadata.tables
    assert "opportunity_products" in Base.metadata.tables


def test_logistics_capability_complements_production_and_export():
    a = _product(uuid4(), "Tomato", "C01")
    b = _product(uuid4(), "Cold Chain", "C11")
    c = _candidate(a, b)
    assert c is not None
    assert set(c["capability_codes"]) == {"C01", "C11"}

    d = _product(uuid4(), "Exporter", "C03")
    e = _product(uuid4(), "Freight", "C11")
    c2 = _candidate(d, e)
    assert c2 is not None
    assert set(c2["capability_codes"]) == {"C03", "C11"}
