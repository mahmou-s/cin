"""Add proactive outreach signal-to-lead workflow.

Revision ID: 0012_proactive_outreach
Revises: 0011_value_chain
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012_proactive_outreach"
down_revision = "0011_value_chain"
branch_labels = None
depends_on = None


def upgrade():
    evidence_kind = postgresql.ENUM("GENERAL", "EXTERNAL_CONTACT_CHANNEL", name="evidence_kind", create_type=False)
    digest_status = postgresql.ENUM("PENDING", "SENT", "FAILED", name="outreach_digest_status", create_type=False)
    bind = op.get_bind()
    bind.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE evidence_kind AS ENUM ('GENERAL', 'EXTERNAL_CONTACT_CHANNEL'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    ))
    bind.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE outreach_digest_status AS ENUM ('PENDING', 'SENT', 'FAILED'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    ))

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("principal_id", sa.String(100), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_principal_id", "users", ["principal_id"], unique=True)

    op.add_column("evidences", sa.Column("evidence_kind", evidence_kind, nullable=False, server_default="GENERAL"))
    op.add_column("evidences", sa.Column("external_entity_ref", sa.String(255), nullable=True))
    op.create_index("ix_evidences_external_entity_ref", "evidences", ["external_entity_ref"])

    op.create_table(
        "outreach_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_content_ref", sa.Text(), nullable=False),
        sa.Column("external_entity_ref", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "source_content_ref", name="uq_outreach_signal_user_content"),
    )
    op.create_index("ix_outreach_signals_user_id", "outreach_signals", ["user_id"])
    op.create_index("ix_outreach_signals_external_entity_ref", "outreach_signals", ["external_entity_ref"])

    op.create_table(
        "outreach_digests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_entity_ref", sa.String(255), nullable=False),
        sa.Column("status", digest_status, nullable=False, server_default="PENDING"),
        sa.Column("scheduled_for", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("cooldown_until", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_outreach_digests_external_entity_ref", "outreach_digests", ["external_entity_ref"])

    op.create_table(
        "outreach_digest_signals",
        sa.Column("digest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("outreach_digests.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("signal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("outreach_signals.id", ondelete="CASCADE"), primary_key=True),
        sa.UniqueConstraint("signal_id", name="uq_outreach_digest_signal"),
    )


def downgrade():
    op.drop_table("outreach_digest_signals")
    op.drop_index("ix_outreach_digests_external_entity_ref", table_name="outreach_digests")
    op.drop_table("outreach_digests")
    op.drop_index("ix_outreach_signals_external_entity_ref", table_name="outreach_signals")
    op.drop_index("ix_outreach_signals_user_id", table_name="outreach_signals")
    op.drop_table("outreach_signals")
    op.drop_index("ix_evidences_external_entity_ref", table_name="evidences")
    op.drop_column("evidences", "external_entity_ref")
    op.drop_column("evidences", "evidence_kind")
    op.drop_index("ix_users_principal_id", table_name="users")
    op.drop_table("users")
    postgresql.ENUM(name="outreach_digest_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="evidence_kind").drop(op.get_bind(), checkfirst=True)
