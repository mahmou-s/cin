from uuid import uuid4
import pytest
from pydantic import ValidationError
from sqlalchemy import inspect

from apps.api.app.models import Base, ActivityDomain, SupportType, VerificationStatus, UserProfile, Product, ProductEvidence, InvestmentSupportRequest
from apps.api.app.schemas import UserProfileCreate, ProductCreate, OwnershipDetailInput


def capacity():
    return {"quantity": 100, "unit": "kg", "delivery_days": 7}


def test_activity_and_support_enums_are_strict():
    profile = UserProfileCreate(
        principal_id="p1", display_name="Demo", activity_domains=[ActivityDomain.AGRICULTURAL]
    )
    assert profile.activity_domains == [ActivityDomain.AGRICULTURAL]
    with pytest.raises(ValidationError):
        UserProfileCreate(principal_id="p2", display_name="Demo", activity_domains=["MINING"])
    with pytest.raises(ValidationError):
        ProductCreate(name="P", category="Workshop", activity_domain="INDUSTRIAL", production_capacity=capacity(), support_types=["LOAN"], ownership=OwnershipDetailInput(asset_type="factory", tenure_type="OWNED"))


def test_agricultural_requires_land_ownership_details():
    with pytest.raises(ValidationError, match="Agricultural"):
        ProductCreate(name="Crop", category="farm", activity_domain=ActivityDomain.AGRICULTURAL, production_capacity=capacity())


def test_industrial_requires_owned_or_leased_asset():
    with pytest.raises(ValidationError, match="Industrial"):
        ProductCreate(name="Factory", category="factory", activity_domain=ActivityDomain.INDUSTRIAL, production_capacity=capacity(), ownership=OwnershipDetailInput(asset_type="factory", tenure_type="OTHER"))


def test_product_evidence_and_investment_request_are_real_orm_models():
    assert ProductEvidence.__tablename__ == "product_evidence"
    assert InvestmentSupportRequest.__tablename__ == "investment_support_requests"
    assert "evidences" in inspect(Product).relationships
    assert {"product", "evidence"}.issubset(inspect(ProductEvidence).relationships.keys())
    assert UserProfile.verification_status.property.columns[0].type.enums == [x.value for x in VerificationStatus]


def test_confidence_is_derived_from_verified_product_evidence():
    p = Product()
    p.evidences = []
    assert p.ai_confidence == (0.0, "UNVERIFIED")
