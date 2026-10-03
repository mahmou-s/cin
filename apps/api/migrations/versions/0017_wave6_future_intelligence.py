"""Wave 6: future intelligence and scenario-aware question signals.
Revision ID: 0017_wave6_future_intelligence
Revises: 0016_question_intelligence_alignment
"""
from alembic import op
import sqlalchemy as sa

revision='0017_wave6_future_intelligence'
down_revision='0016_question_intelligence_alignment'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('client_intelligence_profiles', sa.Column('desired_future', sa.Text(), nullable=True))
    op.add_column('client_intelligence_profiles', sa.Column('future_horizon', sa.String(40), nullable=True))
    op.add_column('client_intelligence_profiles', sa.Column('preferred_scenarios', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('client_intelligence_profiles', sa.Column('readiness_barriers', sa.JSON(), nullable=False, server_default='[]'))
    op.create_table(
        'cin_future_intelligence_signals',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('question_id', sa.UUID(), sa.ForeignKey('cin_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('profile_id', sa.UUID(), sa.ForeignKey('client_intelligence_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.UUID(), sa.ForeignKey('cin_question_sessions.id', ondelete='CASCADE'), nullable=True),
        sa.Column('future_alignment', sa.Float(), nullable=False, server_default='0'),
        sa.Column('scenario_relevance', sa.Float(), nullable=False, server_default='0'),
        sa.Column('readiness_gap', sa.Float(), nullable=False, server_default='0'),
        sa.Column('opportunity_future_signal', sa.Float(), nullable=False, server_default='0'),
        sa.Column('uncertainty_signal', sa.Float(), nullable=False, server_default='0'),
        sa.Column('future_intelligence_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('reason_codes', sa.JSON(), nullable=False),
        sa.Column('context_refs', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_cfqs_question','cin_future_intelligence_signals',['question_id'])
    op.create_index('ix_cfqs_profile','cin_future_intelligence_signals',['profile_id'])
    op.create_index('ix_cfqs_session','cin_future_intelligence_signals',['session_id'])
    op.create_index('ix_cfqs_profile_value','cin_future_intelligence_signals',['profile_id','future_intelligence_value'])

def downgrade():
    op.drop_index('ix_cfqs_profile_value', table_name='cin_future_intelligence_signals')
    op.drop_index('ix_cfqs_session', table_name='cin_future_intelligence_signals')
    op.drop_index('ix_cfqs_profile', table_name='cin_future_intelligence_signals')
    op.drop_index('ix_cfqs_question', table_name='cin_future_intelligence_signals')
    op.drop_table('cin_future_intelligence_signals')
    op.drop_column('client_intelligence_profiles','readiness_barriers')
    op.drop_column('client_intelligence_profiles','preferred_scenarios')
    op.drop_column('client_intelligence_profiles','future_horizon')
    op.drop_column('client_intelligence_profiles','desired_future')
