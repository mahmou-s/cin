"""Harden sovereign business profile/product data model.

Revision ID: 0008_data_model_hardening
Revises: 0007_user_profiles_products
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008_data_model_hardening"
down_revision = "0007_user_profiles_products"
branch_labels = None
depends_on = None

activity_values = ("ECONOMIC", "AGRICULTURAL", "INDUSTRIAL", "SOCIAL", "CULTURAL", "EDUCATIONAL")
support_values = ("GOVERNMENT", "FINANCING", "MARKETING", "CUSTOMS")
verification_values = ("PENDING", "VERIFIED", "REJECTED")


def upgrade():
    # create_type=False avoids double-create when columns bind the same ENUM object.
    activity_enum = postgresql.ENUM(*activity_values, name="activity_domain", create_type=False)
    support_enum = postgresql.ENUM(*support_values, name="support_type", create_type=False)
    verification_enum = postgresql.ENUM(*verification_values, name="verification_status", create_type=False)
    bind = op.get_bind()
    for name, values in (
        ("activity_domain", activity_values),
        ("support_type", support_values),
        ("verification_status", verification_values),
    ):
        vals = ", ".join(f"'{v}'" for v in values)
        bind.execute(sa.text(
            f"DO $$ BEGIN CREATE TYPE {name} AS ENUM ({vals}); "
            f"EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
        ))

    # Preserve existing JSON arrays while converting them to typed PostgreSQL arrays.
    op.add_column("user_profiles", sa.Column("activity_domains_new", postgresql.ARRAY(activity_enum), nullable=True))
    op.execute("""
        UPDATE user_profiles
        SET activity_domains_new = ARRAY(
            SELECT value::activity_domain FROM jsonb_array_elements_text(COALESCE(activity_domains::jsonb, '[]'::jsonb)) AS x(value)
        )
    """)
    op.drop_column("user_profiles", "activity_domains")
    op.alter_column("user_profiles", "activity_domains_new", new_column_name="activity_domains", nullable=False)
    op.add_column("user_profiles", sa.Column("verification_status", verification_enum, nullable=False, server_default="PENDING"))

    op.add_column("products", sa.Column("activity_domain", activity_enum, nullable=True))
    op.execute("UPDATE products SET activity_domain = 'ECONOMIC' WHERE activity_domain IS NULL")
    op.alter_column("products", "activity_domain", nullable=False)
    op.add_column("products", sa.Column("support_types_new", postgresql.ARRAY(support_enum), nullable=True))
    op.execute("""
        UPDATE products
        SET support_types_new = ARRAY(
            SELECT value::support_type FROM jsonb_array_elements_text(COALESCE(support_types::jsonb, '[]'::jsonb)) AS x(value)
        )
    """)
    op.drop_column("products", "support_types")
    op.alter_column("products", "support_types_new", new_column_name="support_types", nullable=False)
    op.add_column("products", sa.Column("verification_status", verification_enum, nullable=False, server_default="PENDING"))

    op.create_table(
        "product_evidence",
        sa.Column("product_id", sa.UUID(), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("evidence_id", sa.UUID(), sa.ForeignKey("evidences.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "investment_support_requests",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("profile_id", sa.UUID(), sa.ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.UUID(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_type", sa.String(40), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("requested_amount", sa.Float()),
        sa.Column("currency", sa.String(12)),
        sa.Column("details", sa.Text()),
        sa.Column("status", verification_enum, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_investment_support_requests_profile_id", "investment_support_requests", ["profile_id"])
    op.create_index("ix_investment_support_requests_product_id", "investment_support_requests", ["product_id"])


def downgrade():
    op.drop_index("ix_investment_support_requests_product_id", table_name="investment_support_requests")
    op.drop_index("ix_investment_support_requests_profile_id", table_name="investment_support_requests")
    op.drop_table("investment_support_requests")
    op.drop_table("product_evidence")

    op.drop_column("products", "verification_status")
    op.add_column("products", sa.Column("support_types_old", sa.JSON(), nullable=True))
    op.execute("""
        UPDATE products SET support_types_old = COALESCE(
            (SELECT json_agg(x) FROM unnest(support_types) AS x), '[]'::json
        )
    """)
    op.drop_column("products", "support_types")
    op.alter_column("products", "support_types_old", new_column_name="support_types", nullable=False)
    op.drop_column("products", "activity_domain")

    op.drop_column("user_profiles", "verification_status")
    op.add_column("user_profiles", sa.Column("activity_domains_old", sa.JSON(), nullable=True))
    op.execute("""
        UPDATE user_profiles SET activity_domains_old = COALESCE(
            (SELECT json_agg(x) FROM unnest(activity_domains) AS x), '[]'::json
        )
    """)
    op.drop_column("user_profiles", "activity_domains")
    op.alter_column("user_profiles", "activity_domains_old", new_column_name="activity_domains", nullable=False)

    postgresql.ENUM(*verification_values, name="verification_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(*support_values, name="support_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(*activity_values, name="activity_domain").drop(op.get_bind(), checkfirst=True)
