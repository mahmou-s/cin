"""Add evidence independence/source grouping key.

Revision ID: 0002_confidence_independence
Revises: 0001_initial_cin
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_confidence_independence"
down_revision = "0001_initial_cin"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "evidences",
        sa.Column("independence_key", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_evidences_independence_key",
        "evidences",
        ["independence_key"],
    )


def downgrade():
    op.drop_index("ix_evidences_independence_key", table_name="evidences")
    op.drop_column("evidences", "independence_key")
