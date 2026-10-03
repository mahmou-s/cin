from pathlib import Path
from apps.api.app.models import Base, ProductComponent, ProductComponentEvidence, ValueChainLink, ValueChainLinkEvidence
from apps.api.app.schemas import ProductComponentCreate, ValueChainLinkCreate

ROOT = Path(__file__).resolve().parents[1]

def test_value_chain_models_and_evidence_links_exist():
    assert ProductComponent.__tablename__ == "product_components"
    assert ProductComponentEvidence.__tablename__ == "product_component_evidence"
    assert ValueChainLink.__tablename__ == "value_chain_links"
    assert ValueChainLinkEvidence.__tablename__ == "value_chain_link_evidence"
    for name in ("product_components", "product_component_evidence", "value_chain_links", "value_chain_link_evidence"):
        assert name in Base.metadata.tables

def test_value_chain_schema_covers_motorcycle_flow():
    component = ProductComponentCreate(component_product_id=__import__('uuid').uuid4(), quantity=2, unit="piece", source_type="EXTERNAL", evidence_ids=[])
    assert component.source_type == "EXTERNAL"
    link = ValueChainLinkCreate(
        from_profile_id=__import__('uuid').uuid4(), to_profile_id=__import__('uuid').uuid4(),
        stage_type="EXPORTER", sequence_order=3, relationship_type="EXPORTS",
    )
    assert link.stage_type == "EXPORTER"
    assert link.sequence_order == 3

def test_value_chain_migration_and_api_are_wired():
    migration = (ROOT / "apps/api/migrations/versions/0011_value_chain.py").read_text()
    api = (ROOT / "apps/api/app/api/v1/value_chain.py").read_text()
    main = (ROOT / "apps/api/app/main.py").read_text()
    page = (ROOT / "apps/web/app/page.js").read_text()
    component = (ROOT / "apps/web/app/components/ValueChainIntelligence.js").read_text()
    assert "down_revision = \"0010_logistics_domain\"" in migration
    assert "product_components" in migration and "value_chain_links" in migration
    assert "/value-chain/products/{product_id}" in api
    assert "value_chain_router" in main
    assert "ValueChainIntelligence" in page
    assert "Product Network · Value Chain" in component

def test_value_chain_stage_types_cover_end_to_end_chain():
    api = (ROOT / "apps/api/app/api/v1/value_chain.py").read_text()
    component = (ROOT / "apps/web/app/components/ValueChainIntelligence.js").read_text()
    for stage in ("SUPPLIER", "MANUFACTURER", "EXPORTER", "IMPORTER", "DISTRIBUTOR", "RETAILER", "SERVICE_PROVIDER"):
        assert stage in component
    assert "sequence_order" in api
    assert "from_product_id" in api and "to_product_id" in api
