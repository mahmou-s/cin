"""Add logistics capability domain and product logistics data.

Revision ID: 0010_logistics_domain
Revises: 0009_opportunity_product_links
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010_logistics_domain"
down_revision = "0009_opportunity_product_links"
branch_labels = None
depends_on = None


def upgrade():
    verification_enum = postgresql.ENUM("PENDING", "VERIFIED", "REJECTED", name="verification_status", create_type=False)
    verification_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "product_logistics_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("origin_country", sa.String(8), nullable=False),
        sa.Column("origin_region", sa.String(120)),
        sa.Column("origin_location", sa.String(255)),
        sa.Column("destination_country", sa.String(8)),
        sa.Column("destination_location", sa.String(255)),
        sa.Column("transport_modes", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("storage_requirements", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("temperature_min_c", sa.Float()),
        sa.Column("temperature_max_c", sa.Float()),
        sa.Column("shelf_life_days", sa.Integer()),
        sa.Column("packaging_requirements", sa.Text()),
        sa.Column("customs_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("insurance_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tracking_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ready_in_days", sa.Integer()),
        sa.Column("notes", sa.Text()),
        sa.Column("verification_status", verification_enum, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_product_logistics_profiles_product_id", "product_logistics_profiles", ["product_id"])

    op.create_table(
        "logistics_routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("origin", sa.String(255), nullable=False),
        sa.Column("destination", sa.String(255), nullable=False),
        sa.Column("mode", sa.String(40), nullable=False),
        sa.Column("distance_km", sa.Float()),
        sa.Column("estimated_days", sa.Float()),
        sa.Column("capacity_quantity", sa.Float()),
        sa.Column("capacity_unit", sa.String(80)),
        sa.Column("cold_chain", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("customs_support", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tracking_available", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verification_status", verification_enum, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_logistics_routes_origin_destination", "logistics_routes", ["origin", "destination"])
    op.create_index("ix_logistics_routes_mode", "logistics_routes", ["mode"])
    op.create_table(
        "logistics_route_evidence",
        sa.Column("route_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("logistics_routes.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evidences.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade():
    op.drop_table("logistics_route_evidence")
    op.drop_index("ix_logistics_routes_mode", table_name="logistics_routes")
    op.drop_index("ix_logistics_routes_origin_destination", table_name="logistics_routes")
    op.drop_table("logistics_routes")
    op.drop_index("ix_product_logistics_profiles_product_id", table_name="product_logistics_profiles")
    op.drop_table("product_logistics_profiles")
