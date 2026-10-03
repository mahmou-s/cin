"""Link products to verified capabilities and opportunities.

Revision ID: 0009_opportunity_product_links
Revises: 0008_data_model_hardening
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_opportunity_product_links"
down_revision = "0008_data_model_hardening"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "product_capability_assertions",
        sa.Column("product_id", sa.UUID(), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("assertion_id", sa.UUID(), sa.ForeignKey("capability_assertions.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_product_capability_assertions_assertion_id", "product_capability_assertions", ["assertion_id"])
    op.create_table(
        "opportunity_products",
        sa.Column("opportunity_id", sa.UUID(), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("product_id", sa.UUID(), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_opportunity_products_product_id", "opportunity_products", ["product_id"])


def downgrade():
    op.drop_index("ix_opportunity_products_product_id", table_name="opportunity_products")
    op.drop_table("opportunity_products")
    op.drop_index("ix_product_capability_assertions_assertion_id", table_name="product_capability_assertions")
    op.drop_table("product_capability_assertions")
