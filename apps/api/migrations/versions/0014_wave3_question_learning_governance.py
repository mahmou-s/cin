"""Wave 3: question learning and governance.
Revision ID: 0014_wave3_question_learning_governance
Revises: 0013_wave2_client_question_intelligence
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision='0014_wave3_question_learning_governance'
down_revision='0013_wave2_client_question_intelligence'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('cin_question_patterns', sa.Column('distinct_session_count', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('cin_question_patterns', sa.Column('candidate_generated_at', sa.DateTime(), nullable=True))
    op.add_column('cin_questions', sa.Column('reviewed_by', sa.String(100), nullable=True))
    op.add_column('cin_questions', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('cin_questions', sa.Column('review_note', sa.Text(), nullable=True))
    op.create_index('ix_cin_question_patterns_segment_occurrence', 'cin_question_patterns', ['segment','occurrence_count'])

def downgrade():
    op.drop_index('ix_cin_question_patterns_segment_occurrence', table_name='cin_question_patterns')
    op.drop_column('cin_questions','review_note')
    op.drop_column('cin_questions','reviewed_at')
    op.drop_column('cin_questions','reviewed_by')
    op.drop_column('cin_question_patterns','candidate_generated_at')
    op.drop_column('cin_question_patterns','distinct_session_count')
