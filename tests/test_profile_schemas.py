from apps.api.app.schemas import UserProfileCreate, ProductCreate
from pydantic import ValidationError
import pytest


def test_profile_and_product_schema_accept_requested_journey():
    profile = UserProfileCreate(
        principal_id="demo-user",
        country_code="EG",
        center="Beba",
        village="Sedes Al Omara",
        display_name="Demo Farm",
        entity_type="COMPANY",
        activity_domains=["AGRICULTURAL", "ECONOMIC"],
    )
    product = ProductCreate(
        name="Fresh Grapes", category="agriculture", activity_domain="AGRICULTURAL", features=["export grade"],
        additional_services=["packaging"], production_capacity={"quantity": 10, "unit": "ton/month", "delivery_days": 14},
        goal="Find an international buyer", support_types=["MARKETING", "CUSTOMS"],
        ownership={"asset_type": "land", "tenure_type": "OWNED", "area": 20, "area_unit": "feddan"},
    )
    assert profile.village == "Sedes Al Omara"
    assert product.production_capacity.quantity == 10
    assert product.ownership.tenure_type == "OWNED"


def test_product_rejects_negative_capacity_and_bad_tenure():
    with pytest.raises(ValidationError):
        ProductCreate(name="X", category="agriculture", production_capacity={"quantity": -1, "unit": "ton"})
    with pytest.raises(ValidationError):
        ProductCreate(name="X", category="agriculture", production_capacity={"quantity": 1, "unit": "ton"}, ownership={"asset_type":"land", "tenure_type":"INVALID"})
