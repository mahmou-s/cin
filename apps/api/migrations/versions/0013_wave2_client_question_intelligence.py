"""Wave 2: client intelligence and adaptive choice-first questioning.
Revision ID: 0013_wave2_client_question_intelligence
Revises: 0012_proactive_outreach
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='0013_wave2_client_question_intelligence'; down_revision='0012_proactive_outreach'; branch_labels=None; depends_on=None

def upgrade():
    client_segment = postgresql.ENUM('INDIVIDUAL','FAMILY_OFFICE','ASSET_MANAGER','PENSION_FUND','INSURER','BANK','CORPORATION','GOVERNMENT','FOUNDATION','HEALTHCARE','UNIVERSITY','FAMILY_BUSINESS','SME','COMMUNITY','OTHER', name='client_segment', create_type=False)
    question_status = postgresql.ENUM('CANDIDATE','VALIDATED','ACTIVE','RETIRED', name='question_status', create_type=False)
    answer_mode = postgresql.ENUM('CHOICE','FREE_TEXT','OTHER', name='answer_mode', create_type=False)
    bind=op.get_bind()
    for sql in [
        "DO $$ BEGIN CREATE TYPE client_segment AS ENUM ('INDIVIDUAL','FAMILY_OFFICE','ASSET_MANAGER','PENSION_FUND','INSURER','BANK','CORPORATION','GOVERNMENT','FOUNDATION','HEALTHCARE','UNIVERSITY','FAMILY_BUSINESS','SME','COMMUNITY','OTHER'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;",
        "DO $$ BEGIN CREATE TYPE question_status AS ENUM ('CANDIDATE','VALIDATED','ACTIVE','RETIRED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;",
        "DO $$ BEGIN CREATE TYPE answer_mode AS ENUM ('CHOICE','FREE_TEXT','OTHER'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;",
    ]: bind.execute(sa.text(sql))
    op.create_table('client_intelligence_profiles',
        sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column('principal_id',sa.String(100),nullable=False),
        sa.Column('segment',client_segment,nullable=False,server_default='OTHER'),
        sa.Column('organization_size',sa.String(40)),
        sa.Column('strategic_objectives',postgresql.JSONB,nullable=False,server_default='[]'),
        sa.Column('constraints',postgresql.JSONB,nullable=False,server_default='[]'),
        sa.Column('decision_horizon',sa.String(40)),
        sa.Column('readiness_level',sa.String(40)),
        sa.Column('profile_confidence',sa.Float,nullable=False,server_default='0'),
        sa.Column('source',sa.Text,nullable=True),
        sa.Column('created_at',sa.DateTime,nullable=False), sa.Column('updated_at',sa.DateTime,nullable=False),
        sa.UniqueConstraint('principal_id',name='uq_client_intelligence_profiles_principal'))
    op.create_index('ix_client_intelligence_profiles_segment','client_intelligence_profiles',['segment'])
    op.create_table('cin_questions',
        sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column('question_key',sa.String(160),nullable=False,unique=True),
        sa.Column('segment',client_segment,nullable=False),
        sa.Column('text',sa.Text,nullable=False),
        sa.Column('options',postgresql.JSONB,nullable=False,server_default='[]'),
        sa.Column('allow_free_text',sa.Boolean,nullable=False,server_default='true'),
        sa.Column('status',question_status,nullable=False,server_default='ACTIVE'),
        sa.Column('priority',sa.Integer,nullable=False,server_default='100'),
        sa.Column('usage_count',sa.Integer,nullable=False,server_default='0'),
        sa.Column('created_from_pattern',sa.String(255)),
        sa.Column('created_at',sa.DateTime,nullable=False), sa.Column('updated_at',sa.DateTime,nullable=False))
    op.create_index('ix_cin_questions_segment_status','cin_questions',['segment','status'])
    op.create_table('cin_question_sessions',
        sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column('principal_id',sa.String(100),nullable=False),
        sa.Column('segment',client_segment,nullable=False),
        sa.Column('current_question_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('cin_questions.id',ondelete='SET NULL')),
        sa.Column('completed',sa.Boolean,nullable=False,server_default='false'),
        sa.Column('created_at',sa.DateTime,nullable=False), sa.Column('updated_at',sa.DateTime,nullable=False))
    op.create_index('ix_cin_question_sessions_principal','cin_question_sessions',['principal_id'])
    op.create_table('cin_question_answers',
        sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column('session_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('cin_question_sessions.id',ondelete='CASCADE'),nullable=False),
        sa.Column('question_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('cin_questions.id',ondelete='CASCADE'),nullable=False),
        sa.Column('mode',answer_mode,nullable=False),
        sa.Column('selected_option',sa.String(255)),
        sa.Column('free_text',sa.Text),
        sa.Column('extracted_concepts',postgresql.JSONB,nullable=False,server_default='[]'),
        sa.Column('created_at',sa.DateTime,nullable=False))
    op.create_index('ix_cin_question_answers_question','cin_question_answers',['question_id'])
    op.create_table('cin_question_patterns',
        sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column('concept_key',sa.String(180),nullable=False),
        sa.Column('normalized_text',sa.Text,nullable=False),
        sa.Column('segment',client_segment,nullable=False),
        sa.Column('occurrence_count',sa.Integer,nullable=False,server_default='1'),
        sa.Column('candidate_question_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('cin_questions.id',ondelete='SET NULL')),
        sa.Column('validated',sa.Boolean,nullable=False,server_default='false'),
        sa.Column('created_at',sa.DateTime,nullable=False), sa.Column('updated_at',sa.DateTime,nullable=False),
        sa.UniqueConstraint('concept_key','segment',name='uq_cin_question_patterns_concept_segment'))

def downgrade():
    for t in ['cin_question_patterns','cin_question_answers','cin_question_sessions','cin_questions','client_intelligence_profiles']: op.drop_table(t)
    for n in ['answer_mode','question_status','client_segment']: postgresql.ENUM(name=n).drop(op.get_bind(),checkfirst=True)
