from pathlib import Path
from apps.api.app.models import Base, LogisticsRoute, LogisticsRouteEvidence, ProductLogisticsProfile
from apps.api.app.schemas import LogisticsProfileCreate, LogisticsRouteCreate

ROOT = Path(__file__).resolve().parents[1]

def test_logistics_models_and_join_table_exist():
    assert ProductLogisticsProfile.__tablename__ == "product_logistics_profiles"
    assert LogisticsRoute.__tablename__ == "logistics_routes"
    assert LogisticsRouteEvidence.__tablename__ == "logistics_route_evidence"
    assert "product_logistics_profiles" in Base.metadata.tables
    assert "logistics_routes" in Base.metadata.tables
    assert "logistics_route_evidence" in Base.metadata.tables

def test_logistics_schema_covers_local_and_international_requirements():
    profile = LogisticsProfileCreate(
        origin_country="EG", origin_region="Beni Suef", origin_location="Village",
        destination_country="SA", destination_location="Riyadh",
        transport_modes=["ROAD", "SEA"], storage_requirements=["COLD_STORAGE"],
        temperature_min_c=2, temperature_max_c=8, shelf_life_days=30,
        customs_required=True, insurance_required=True, tracking_required=True,
    )
    assert profile.destination_country == "SA"
    assert "COLD_STORAGE" in profile.storage_requirements
    route = LogisticsRouteCreate(origin="Beni Suef", destination="Riyadh", mode="MULTIMODAL", customs_support=True, tracking_available=True)
    assert route.mode == "MULTIMODAL"
    assert route.customs_support is True

def test_logistics_migration_and_seed_include_c11():
    migration = (ROOT / "apps/api/migrations/versions/0010_logistics_domain.py").read_text()
    seed = (ROOT / "apps/api/app/seed.py").read_text()
    assert "0010_logistics_domain" in migration
    assert "product_logistics_profiles" in migration
    assert "logistics_routes" in migration
    assert '("C11","Logistics Capability")' in seed

def test_logistics_api_and_homepage_are_wired():
    api = (ROOT / "apps/api/app/api/v1/logistics.py").read_text()
    main = (ROOT / "apps/api/app/main.py").read_text()
    page = (ROOT / "apps/web/app/page.js").read_text()
    component = (ROOT / "apps/web/app/components/LogisticsIntelligence.js").read_text()
    assert '/logistics/products/{product_id}' in api
    assert '/logistics/routes' in api
    assert 'logistics_router' in main
    assert 'LogisticsIntelligence' in page
    assert 'href="#logistics"' in page
    assert 'C11 · Logistics Capability' in component
