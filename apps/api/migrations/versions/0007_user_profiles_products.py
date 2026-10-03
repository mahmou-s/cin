"""Add sovereign business profile, product, capacity and ownership models.

Revision ID: 0007_user_profiles_products
Revises: 0006_outbox_backoff
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_user_profiles_products"
down_revision = "0006_outbox_backoff"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("principal_id", sa.String(100), nullable=False),
        sa.Column("country_code", sa.String(8), nullable=False, server_default="EG"),
        sa.Column("governorate", sa.String(120)), sa.Column("center", sa.String(120)), sa.Column("village", sa.String(120)),
        sa.Column("national_id", sa.String(64)), sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("organization_name", sa.String(255)), sa.Column("commercial_register", sa.String(120)),
        sa.Column("entity_type", sa.String(40), nullable=False, server_default="INDIVIDUAL"),
        sa.Column("activity_domains", sa.JSON(), nullable=False), sa.Column("bio", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_user_profiles_principal_id", "user_profiles", ["principal_id"], unique=True)
    op.create_unique_constraint("uq_user_profiles_national_id", "user_profiles", ["national_id"])

    op.create_table(
        "products",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("profile_id", sa.UUID(), sa.ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False), sa.Column("category", sa.String(80), nullable=False),
        sa.Column("description", sa.Text()), sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("additional_services", sa.JSON(), nullable=False), sa.Column("media", sa.JSON(), nullable=False),
        sa.Column("documents", sa.JSON(), nullable=False), sa.Column("goal", sa.Text()),
        sa.Column("support_types", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_products_profile_id", "products", ["profile_id"])

    op.create_table(
        "production_capacities",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("product_id", sa.UUID(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False), sa.Column("unit", sa.String(80), nullable=False),
        sa.Column("quality_description", sa.Text()), sa.Column("commitment_volume", sa.Float()),
        sa.Column("commitment_unit", sa.String(80)), sa.Column("delivery_days", sa.Integer()),
        sa.Column("delivery_term", sa.String(120)), sa.Column("measurement_period", sa.String(80)),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_unique_constraint("uq_production_capacities_product_id", "production_capacities", ["product_id"])

    op.create_table(
        "ownership_details",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("profile_id", sa.UUID(), sa.ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.UUID(), sa.ForeignKey("products.id", ondelete="CASCADE")),
        sa.Column("asset_type", sa.String(50), nullable=False), sa.Column("tenure_type", sa.String(30), nullable=False),
        sa.Column("area", sa.Float()), sa.Column("area_unit", sa.String(40)), sa.Column("notes", sa.Text()),
    )
    op.create_index("ix_ownership_details_profile_id", "ownership_details", ["profile_id"])
    op.create_index("ix_ownership_details_product_id", "ownership_details", ["product_id"])


def downgrade():
    op.drop_index("ix_ownership_details_product_id", table_name="ownership_details")
    op.drop_index("ix_ownership_details_profile_id", table_name="ownership_details")
    op.drop_table("ownership_details")
    op.drop_constraint("uq_production_capacities_product_id", "production_capacities", type_="unique")
    op.drop_table("production_capacities")
    op.drop_index("ix_products_profile_id", table_name="products")
    op.drop_table("products")
    op.drop_constraint("uq_user_profiles_national_id", "user_profiles", type_="unique")
    op.drop_index("ix_user_profiles_principal_id", table_name="user_profiles")
    op.drop_table("user_profiles")
