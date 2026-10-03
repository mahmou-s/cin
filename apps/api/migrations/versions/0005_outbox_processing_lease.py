"""Track outbox processing start time for crash recovery.

Revision ID: 0005_outbox_processing_lease
Revises: 0004_confidence_audit_and_submitter
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0005_outbox_processing_lease"
down_revision: Union[str, None] = "0004_confidence_audit_and_submitter"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("transactional_outbox", sa.Column("processing_started_at", sa.DateTime(), nullable=True))
    op.create_index("ix_outbox_processing_started_at", "transactional_outbox", ["processing_started_at"])


def downgrade() -> None:
    op.drop_index("ix_outbox_processing_started_at", table_name="transactional_outbox")
    op.drop_column("transactional_outbox", "processing_started_at")
