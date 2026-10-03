"""Wave 4: question knowledge graph and evidence-aware prioritization.
Revision ID: 0015_wave4_question_knowledge_graph
Revises: 0014_wave3_question_learning_governance
"""
from alembic import op
import sqlalchemy as sa

revision='0015_wave4_question_knowledge_graph'
down_revision='0014_wave3_question_learning_governance'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table(
        'cin_question_knowledge_links',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('question_id', sa.UUID(), sa.ForeignKey('cin_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_key', sa.String(180), nullable=False),
        sa.Column('concept_type', sa.String(40), nullable=False, server_default='CONCEPT'),
        sa.Column('entity_ref', sa.String(255), nullable=True),
        sa.Column('evidence_state', sa.String(30), nullable=False, server_default='UNKNOWN'),
        sa.Column('relevance_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_cin_qkg_question', 'cin_question_knowledge_links', ['question_id'])
    op.create_index('ix_cin_qkg_concept', 'cin_question_knowledge_links', ['concept_key'])
    op.create_table(
        'cin_question_priority_signals',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('question_id', sa.UUID(), sa.ForeignKey('cin_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('profile_id', sa.UUID(), sa.ForeignKey('client_intelligence_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('objective_match', sa.Float(), nullable=False, server_default='0'),
        sa.Column('constraint_match', sa.Float(), nullable=False, server_default='0'),
        sa.Column('pattern_signal', sa.Float(), nullable=False, server_default='0'),
        sa.Column('evidence_signal', sa.Float(), nullable=False, server_default='0'),
        sa.Column('novelty_signal', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('reason_codes', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_cin_qps_profile_score', 'cin_question_priority_signals', ['profile_id', 'total_score'])

def downgrade():
    op.drop_index('ix_cin_qps_profile_score', table_name='cin_question_priority_signals')
    op.drop_table('cin_question_priority_signals')
    op.drop_index('ix_cin_qkg_concept', table_name='cin_question_knowledge_links')
    op.drop_index('ix_cin_qkg_question', table_name='cin_question_knowledge_links')
    op.drop_table('cin_question_knowledge_links')
