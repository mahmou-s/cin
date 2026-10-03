"""Store reviewer evidence assessments as first-class records.

Revision ID: 0003_evidence_assessments
Revises: 0002_confidence_independence
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_evidence_assessments"
down_revision: Union[str, None] = "0002_confidence_independence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def uuid_col():
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "evidence_assessments",
        sa.Column("id", uuid_col(), primary_key=True, nullable=False),
        sa.Column("assertion_id", uuid_col(), sa.ForeignKey("capability_assertions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_id", uuid_col(), sa.ForeignKey("evidences.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer", sa.String(100), nullable=False),
        sa.Column("authority", sa.Float(), nullable=False),
        sa.Column("directness", sa.Float(), nullable=False),
        sa.Column("recency", sa.Float(), nullable=False),
        sa.Column("validation", sa.Float(), nullable=False),
        sa.Column("consistency", sa.Float(), nullable=False),
        sa.Column("independence", sa.Float(), nullable=False),
        sa.Column("completeness", sa.Float(), nullable=False),
        sa.Column("independence_key", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_evidence_assessments_assertion_evidence",
        "evidence_assessments",
        ["assertion_id", "evidence_id"],
    )
    op.create_index(
        "ix_evidence_assessments_assertion_id",
        "evidence_assessments",
        ["assertion_id"],
    )
    op.create_index(
        "ix_evidence_assessments_evidence_id",
        "evidence_assessments",
        ["evidence_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_evidence_assessments_evidence_id", table_name="evidence_assessments")
    op.drop_index("ix_evidence_assessments_assertion_id", table_name="evidence_assessments")
    op.drop_index("ix_evidence_assessments_assertion_evidence", table_name="evidence_assessments")
    op.drop_table("evidence_assessments")
