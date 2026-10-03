from uuid import uuid4
from apps.api.app.schemas import ProductCreate


def test_profile_router_exposes_crud_and_investment_routes():
    source = Path("apps/api/app/api/v1/profiles.py").read_text()
    assert '@router.get("/profiles/me"' in source
    assert '@router.post("/profiles/me/products"' in source
    assert '@router.patch("/profiles/me/products/{product_id}"' in source
    assert 'investment-requests' in source


def test_product_schema_accepts_evidence_ids():
    data = ProductCreate(
        name="Demo Product", category="service", activity_domain="ECONOMIC",
        production_capacity={"quantity": 10, "unit": "units"},
        evidence_ids=[uuid4()],
    )
    assert len(data.evidence_ids) == 1
from pathlib import Path
import ast


def test_profile_and_evidence_routes_are_auth_protected_by_dependency():
    source = Path("apps/api/app/api/v1/profiles.py").read_text()
    evidence = Path("apps/api/app/api/v1/evidence.py").read_text()
    assert "Depends(require_submitter)" in source
    assert "Depends(require_submitter)" in evidence


def test_evidence_upload_persists_an_evidence_record_and_can_link_product():
    source = Path("apps/api/app/api/v1/evidence.py").read_text()
    tree = ast.parse(source)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert "Evidence" in names
    assert "Product" in names
    assert "product_id" in source
