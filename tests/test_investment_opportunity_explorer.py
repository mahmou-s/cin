from types import SimpleNamespace
from uuid import uuid4
from uuid import uuid4

from apps.api.app.services.investment_opportunity_explorer import _candidate, _need_signals, _capacity


def _evidence(status="VERIFIED"):
    return SimpleNamespace(id=uuid4(), validation_status=status)


def _assertion(code, evidence):
    return SimpleNamespace(
        id=uuid4(), status="VERIFIED", confidence_score=0.82,
        capability_type=SimpleNamespace(code=code, name=code), evidences=[evidence],
    )


def _product(profile_id, name, code, evidence_status="VERIFIED"):
    evidence = _evidence(evidence_status)
    return SimpleNamespace(
        id=uuid4(), profile_id=profile_id, name=name, category="demo",
        description="food product", goal="export and financing",
        support_types=[SimpleNamespace(value="FINANCING")],
        evidences=[evidence],
        capability_assertions=[_assertion(code, evidence)],
        investment_requests=[SimpleNamespace(
            id=uuid4(), status="VERIFIED", request_type="FINANCING",
            goal="working capital", requested_amount=100000.0, currency="EGP", details="demo"
        )],
        production_capacity=SimpleNamespace(
            quantity=1000, unit="kg", quality_description="A", commitment_volume=500,
            commitment_unit="kg", delivery_days=10, delivery_term="FOB", measurement_period="month"
        ),
    )


def test_explorer_candidate_requires_verified_product_evidence_and_capability():
    a = _product(uuid4(), "Farm Product", "C01")
    b = _product(uuid4(), "Export Service", "C03")
    candidate = _candidate(a, b)
    assert candidate is not None
    assert candidate["capability_codes"] == ["C01", "C03"]
    assert candidate["confidence_floor"] == 0.82
    assert len(candidate["verified_evidence_ids"]) >= 2


def test_explorer_rejects_unverified_evidence():
    a = _product(uuid4(), "Farm Product", "C01")
    b = _product(uuid4(), "Export Service", "C03", evidence_status="PENDING")
    assert _candidate(a, b) is None


def test_need_signals_are_explicit_and_traceable():
    p = _product(uuid4(), "Product", "C01")
    signals = _need_signals(p)
    assert any(s["type"] == "PRODUCT_GOAL" for s in signals)
    assert any(s["type"] == "SUPPORT_REQUEST" and "source_id" in s for s in signals)


def test_capacity_is_context_not_score():
    p = _product(uuid4(), "Product", "C01")
    capacity = _capacity(p)
    assert capacity["quantity"] == 1000
    assert capacity["commitment_volume"] == 500
    assert "score" not in capacity

import asyncio
from types import SimpleNamespace

from apps.api.app.services.investment_opportunity_explorer import explore_investment_opportunities


class _ScalarResult:
    def __init__(self, items):
        self._items = list(items)

    def all(self):
        return list(self._items)

    def scalars(self):
        return self


def uuid4_from_string(value):
    from uuid import UUID
    return UUID(value)


class _IntegrationSession:
    """Service-level integration harness: executes the real explorer function."""
    def __init__(self, products, existing_opportunity=None, existing_product_ids=None):
        self.products = products
        self.added = []
        self.committed = False
        self.existing_opportunity = existing_opportunity
        self.existing_product_ids = {str(x) for x in (existing_product_ids or [])}
        self.execute_calls = 0

    async def scalars(self, stmt):
        # The real function constructs the SQL verification/activity predicates;
        # this harness supplies the persisted VERIFIED product rows, then the
        # function's Python-side filters are exercised as defense-in-depth.
        return _ScalarResult(self.products)

    async def execute(self, stmt):
        self.execute_calls += 1
        # The first exploration has no existing row. After it persists an Opportunity,
        # the second exploration sees the constructor-supplied existing row, then the
        # linked-product lookup returns the same product set.
        if self.existing_opportunity is not None and self.added and self.execute_calls >= 2:
            if self.execute_calls == 2:
                return _ScalarResult([self.existing_opportunity])
            return _ScalarResult([uuid4_from_string(x) for x in sorted(self.existing_product_ids)])
        return _ScalarResult([])

    def add(self, obj):
        self.added.append(obj)

    def add_all(self, objects):
        self.added.extend(objects)

    async def flush(self):
        for obj in self.added:
            if hasattr(obj, "id") and getattr(obj, "id", None) is None:
                if obj.__class__.__name__ == "Opportunity" and self.existing_opportunity is not None:
                    obj.id = self.existing_opportunity.id
                else:
                    obj.id = uuid4()

    async def commit(self):
        self.committed = True


def _integration_product(profile_id, name, code, *, domain="AGRICULTURAL", support="FINANCING", text="tomato"):
    p = _product(profile_id, name, code)
    p.verification_status = "VERIFIED"
    p.activity_domain = SimpleNamespace(value=domain)
    p.support_types = [SimpleNamespace(value=support)]
    p.category = "food"
    p.description = f"verified {text} product"
    p.goal = f"{text} market expansion"
    return p


def test_explore_integration_query_filters_real_function_and_excludes_nonmatching_products():
    a = _integration_product(uuid4(), "Tomato Farm", "C01", text="tomato")
    b = _integration_product(uuid4(), "Tomato Export", "C03", text="tomato")
    wrong = _integration_product(uuid4(), "Coffee Export", "C03", text="coffee")
    db = _IntegrationSession([a, b, wrong])

    results = asyncio.run(explore_investment_opportunities(db, query="tomato"))

    assert len(results) == 1
    assert {x["name"] for x in results[0]["products"]} == {"Tomato Farm", "Tomato Export"}
    assert "Coffee Export" not in {x["name"] for x in results[0]["products"]}
    assert db.committed is True
    assert results[0]["opportunity_id"]
    persisted = [x for x in db.added if x.__class__.__name__ == "Opportunity"]
    assert len(persisted) == 1
    assert persisted[0].status == "POTENTIAL"
    assert any(x.__class__.__name__ == "ReasoningRun" for x in db.added)


def test_explore_integration_activity_domain_and_support_type_filters_work():
    a = _integration_product(uuid4(), "Farm", "C01", domain="AGRICULTURAL", support="FINANCING")
    b = _integration_product(uuid4(), "Exporter", "C03", domain="AGRICULTURAL", support="FINANCING")
    wrong_domain = _integration_product(uuid4(), "Other Exporter", "C03", domain="INDUSTRIAL", support="FINANCING")
    wrong_support = _integration_product(uuid4(), "Marketing Exporter", "C03", domain="AGRICULTURAL", support="MARKETING")

    db = _IntegrationSession([a, b, wrong_domain, wrong_support])
    results = asyncio.run(explore_investment_opportunities(
        db, activity_domain="AGRICULTURAL", support_type="FINANCING"
    ))

    assert len(results) == 1
    assert {str(x["id"]) for x in results[0]["products"]} == {str(a.id), str(b.id)}


def test_explore_integration_returns_empty_without_verified_products():
    pending = _integration_product(uuid4(), "Pending Farm", "C01")
    pending.verification_status = "PENDING"
    db = _IntegrationSession([pending])

    results = asyncio.run(explore_investment_opportunities(db))

    assert results == []
    assert db.added == []
    assert db.committed is False

import pytest


@pytest.mark.parametrize("field", ["name", "category", "description", "goal"])
def test_explore_integration_query_searches_each_required_text_field(field):
    a = _integration_product(uuid4(), "Farm", "C01", text="neutral")
    b = _integration_product(uuid4(), "Exporter", "C03", text="neutral")
    marker = "needle"
    setattr(a, field, marker)
    setattr(b, field, marker)
    wrong = _integration_product(uuid4(), "Unrelated", "C03", text="other")
    db = _IntegrationSession([a, b, wrong])

    results = asyncio.run(explore_investment_opportunities(db, query=marker))

    assert len(results) == 1
    assert {str(x["id"]) for x in results[0]["products"]} == {str(a.id), str(b.id)}


def test_explore_integration_reuses_existing_opportunity_for_same_product_set():
    a = _integration_product(uuid4(), "Tomato Farm", "C01", text="tomato")
    b = _integration_product(uuid4(), "Tomato Export", "C03", text="tomato")
    from apps.api.app.models import Opportunity

    existing = Opportunity(
        id=uuid4(),
        title="Existing tomato opportunity",
        opportunity_type="INVESTMENT_COLLABORATION_EXPLORATION",
        status="POTENTIAL",
        description="existing",
        rationale={},
    )
    db = _IntegrationSession(
        [a, b],
        existing_opportunity=existing,
        existing_product_ids=[a.id, b.id],
    )

    first = asyncio.run(explore_investment_opportunities(db, query="tomato"))
    second = asyncio.run(explore_investment_opportunities(db, query="tomato"))

    assert first[0]["opportunity_id"] == str(existing.id)
    assert second[0]["opportunity_id"] == str(existing.id)
    persisted = [x for x in db.added if x.__class__.__name__ == "Opportunity"]
    assert len(persisted) == 1
    assert persisted[0].id == existing.id
    assert len([x for x in db.added if x.__class__.__name__ == "OpportunityProduct"]) == 2

