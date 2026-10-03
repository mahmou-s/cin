"""Wave 5: align question prioritization with capability, evidence, opportunity, need and risk context.
Revision ID: 0016_question_intelligence_alignment
Revises: 0015_wave4_question_knowledge_graph
"""
from alembic import op
import sqlalchemy as sa

revision='0016_question_intelligence_alignment'
down_revision='0015_wave4_question_knowledge_graph'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table(
        'cin_question_intelligence_signals',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('question_id', sa.UUID(), sa.ForeignKey('cin_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('profile_id', sa.UUID(), sa.ForeignKey('client_intelligence_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.UUID(), sa.ForeignKey('cin_question_sessions.id', ondelete='CASCADE'), nullable=True),
        sa.Column('capability_signal', sa.Float(), nullable=False, server_default='0'),
        sa.Column('evidence_gap_signal', sa.Float(), nullable=False, server_default='0'),
        sa.Column('opportunity_signal', sa.Float(), nullable=False, server_default='0'),
        sa.Column('need_signal', sa.Float(), nullable=False, server_default='0'),
        sa.Column('risk_signal', sa.Float(), nullable=False, server_default='0'),
        sa.Column('intelligence_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('reason_codes', sa.JSON(), nullable=False),
        sa.Column('context_refs', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_cqis_question', 'cin_question_intelligence_signals', ['question_id'])
    op.create_index('ix_cqis_profile', 'cin_question_intelligence_signals', ['profile_id'])
    op.create_index('ix_cqis_session', 'cin_question_intelligence_signals', ['session_id'])
    op.create_index('ix_cqis_profile_value', 'cin_question_intelligence_signals', ['profile_id','intelligence_value'])

def downgrade():
    op.drop_index('ix_cqis_profile_value', table_name='cin_question_intelligence_signals')
    op.drop_index('ix_cqis_session', table_name='cin_question_intelligence_signals')
    op.drop_index('ix_cqis_profile', table_name='cin_question_intelligence_signals')
    op.drop_index('ix_cqis_question', table_name='cin_question_intelligence_signals')
    op.drop_table('cin_question_intelligence_signals')
