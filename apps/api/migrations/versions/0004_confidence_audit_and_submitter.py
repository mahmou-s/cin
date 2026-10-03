"""Persist confidence raw score/gate reasons and submission principal.

Revision ID: 0004_confidence_audit_and_submitter
Revises: 0003_evidence_assessments
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004_confidence_audit_and_submitter"
down_revision: Union[str, None] = "0003_evidence_assessments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("capability_assertions", sa.Column("confidence_raw_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("capability_assertions", sa.Column("confidence_gate_reasons", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("capability_assertions", sa.Column("submitted_by", sa.String(100), nullable=True))
    op.create_index("ix_assertions_submitted_by", "capability_assertions", ["submitted_by"])


def downgrade() -> None:
    op.drop_index("ix_assertions_submitted_by", table_name="capability_assertions")
    op.drop_column("capability_assertions", "submitted_by")
    op.drop_column("capability_assertions", "confidence_gate_reasons")
    op.drop_column("capability_assertions", "confidence_raw_score")
