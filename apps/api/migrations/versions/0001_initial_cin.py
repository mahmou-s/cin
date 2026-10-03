"""Initial CIN production schema.

Revision ID: 0001_initial_cin
Revises: None
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_cin"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def uuid_col():
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table("communities",
        sa.Column("id", uuid_col(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country_code", sa.String(8), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("population", sa.Integer()),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_communities_country_code", "communities", ["country_code"])

    op.create_table("capability_types",
        sa.Column("id", uuid_col(), primary_key=True, nullable=False),
        sa.Column("code", sa.String(8), nullable=False, unique=True),
        sa.Column("domain", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
    )
    op.create_index("ix_capability_types_domain", "capability_types", ["domain"])

    op.create_table("capability_assertions",
        sa.Column("id", uuid_col(), primary_key=True, nullable=False),
        sa.Column("community_id", uuid_col(), sa.ForeignKey("communities.id"), nullable=False),
        sa.Column("capability_type_id", uuid_col(), sa.ForeignKey("capability_types.id"), nullable=False),
        sa.Column("scope", sa.String(255)),
        sa.Column("scale", sa.String(100)),
        sa.Column("quantity", sa.Float()),
        sa.Column("unit", sa.String(100)),
        sa.Column("measurement_period", sa.String(100)),
        sa.Column("maturity_level", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("confidence_level", sa.String(30), nullable=False),
        sa.Column("conflict_flag", sa.Boolean(), nullable=False),
        sa.Column("review_note", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime()),
        sa.Column("reviewed_by", sa.String(100)),
    )
    op.create_index("ix_assertions_status", "capability_assertions", ["status"])
    op.create_index("ix_assertions_community", "capability_assertions", ["community_id"])

    op.create_table("evidences",
        sa.Column("id", uuid_col(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("evidence_type", sa.String(50), nullable=False),
        sa.Column("original_filename", sa.String(255)),
        sa.Column("content_url", sa.Text()),
        sa.Column("content_text", sa.Text()),
        sa.Column("sha256", sa.String(64)),
        sa.Column("mime_type", sa.String(150)),
        sa.Column("size_bytes", sa.Integer()),
        sa.Column("validation_status", sa.String(30), nullable=False),
        sa.Column("authority", sa.Float(), nullable=False),
        sa.Column("directness", sa.Float(), nullable=False),
        sa.Column("recency", sa.Float(), nullable=False),
        sa.Column("validation", sa.Float(), nullable=False),
        sa.Column("consistency", sa.Float(), nullable=False),
        sa.Column("independence", sa.Float(), nullable=False),
        sa.Column("completeness", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_evidences_sha256", "evidences", ["sha256"])

    op.create_table("assertion_evidence",
        sa.Column("assertion_id", uuid_col(), sa.ForeignKey("capability_assertions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("evidence_id", uuid_col(), sa.ForeignKey("evidences.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table("validation_events",
        sa.Column("id", uuid_col(), primary_key=True, nullable=False),
        sa.Column("assertion_id", uuid_col(), sa.ForeignKey("capability_assertions.id"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_validation_events_assertion", "validation_events", ["assertion_id"])

    op.create_table("transactional_outbox",
        sa.Column("id", uuid_col(), primary_key=True, nullable=False),
        sa.Column("aggregate_type", sa.String(80), nullable=False),
        sa.Column("aggregate_id", uuid_col(), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime()),
    )
    op.create_index("ix_outbox_status_created", "transactional_outbox", ["status", "created_at"])
    op.create_index("ix_outbox_aggregate", "transactional_outbox", ["aggregate_type", "aggregate_id"])

    op.create_table("opportunities",
        sa.Column("id", uuid_col(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("opportunity_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rationale", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table("opportunity_reviews",
        sa.Column("id", uuid_col(), primary_key=True, nullable=False),
        sa.Column("opportunity_id", uuid_col(), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision", sa.String(30), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_opportunity_reviews_opportunity", "opportunity_reviews", ["opportunity_id"])

    op.create_table("opportunity_assertions",
        sa.Column("opportunity_id", uuid_col(), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("assertion_id", uuid_col(), sa.ForeignKey("capability_assertions.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table("reasoning_runs",
        sa.Column("id", uuid_col(), primary_key=True, nullable=False),
        sa.Column("opportunity_id", uuid_col(), sa.ForeignKey("opportunities.id", ondelete="CASCADE")),
        sa.Column("engine", sa.String(120), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_reasoning_runs_opportunity", "reasoning_runs", ["opportunity_id"])

    op.create_table("scenarios",
        sa.Column("id", uuid_col(), primary_key=True, nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("requested_codes", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table("scenario_steps",
        sa.Column("id", uuid_col(), primary_key=True, nullable=False),
        sa.Column("scenario_id", uuid_col(), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("assertion_id", uuid_col(), sa.ForeignKey("capability_assertions.id"), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("support_score", sa.Float(), nullable=False),
    )
    op.create_index("ix_scenario_steps_scenario", "scenario_steps", ["scenario_id"])


def downgrade() -> None:
    for table in [
        "scenario_steps", "scenarios", "reasoning_runs", "opportunity_assertions",
        "opportunity_reviews", "opportunities", "transactional_outbox",
        "validation_events", "assertion_evidence", "evidences",
        "capability_assertions", "capability_types", "communities",
    ]:
        op.drop_table(table)
