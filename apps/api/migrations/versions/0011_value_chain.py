"""Add product components and value-chain links.

Revision ID: 0011_value_chain
Revises: 0010_logistics_domain
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011_value_chain"
down_revision = "0010_logistics_domain"
branch_labels = None
depends_on = None


def upgrade():
    verification_enum = postgresql.ENUM("PENDING", "VERIFIED", "REJECTED", name="verification_status", create_type=False)
    verification_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "product_components",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("component_product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Float()),
        sa.Column("unit", sa.String(80)),
        sa.Column("source_type", sa.String(20), nullable=False, server_default="EXTERNAL"),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text()),
        sa.Column("verification_status", verification_enum, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_product_components_product_id", "product_components", ["product_id"])
    op.create_index("ix_product_components_component_product_id", "product_components", ["component_product_id"])

    op.create_table(
        "value_chain_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("to_product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("stage_type", sa.String(40), nullable=False),
        sa.Column("sequence_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("relationship_type", sa.String(50), nullable=False, server_default="SUPPLIES"),
        sa.Column("notes", sa.Text()),
        sa.Column("verification_status", verification_enum, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_value_chain_links_product_id", "value_chain_links", ["product_id"])
    op.create_index("ix_value_chain_links_from_profile_id", "value_chain_links", ["from_profile_id"])
    op.create_index("ix_value_chain_links_to_profile_id", "value_chain_links", ["to_profile_id"])
    op.create_index("ix_value_chain_links_sequence", "value_chain_links", ["product_id", "sequence_order"])
    op.create_table(
        "product_component_evidence",
        sa.Column("component_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_components.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evidences.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "value_chain_link_evidence",
        sa.Column("link_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("value_chain_links.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evidences.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade():
    op.drop_table("value_chain_link_evidence")
    op.drop_table("product_component_evidence")
    op.drop_index("ix_value_chain_links_sequence", table_name="value_chain_links")
    op.drop_index("ix_value_chain_links_to_profile_id", table_name="value_chain_links")
    op.drop_index("ix_value_chain_links_from_profile_id", table_name="value_chain_links")
    op.drop_index("ix_value_chain_links_product_id", table_name="value_chain_links")
    op.drop_table("value_chain_links")
    op.drop_index("ix_product_components_component_product_id", table_name="product_components")
    op.drop_index("ix_product_components_product_id", table_name="product_components")
    op.drop_table("product_components")
