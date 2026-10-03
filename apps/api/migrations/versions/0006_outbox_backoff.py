from alembic import op
import sqlalchemy as sa
revision='0006_outbox_backoff'; down_revision='0005_outbox_processing_lease'; branch_labels=None; depends_on=None
def upgrade():
    op.add_column('transactional_outbox',sa.Column('next_attempt_at',sa.DateTime(),nullable=True))
    op.create_index('ix_transactional_outbox_next_attempt_at','transactional_outbox',['next_attempt_at'])
def downgrade():
    op.drop_index('ix_transactional_outbox_next_attempt_at',table_name='transactional_outbox')
    op.drop_column('transactional_outbox','next_attempt_at')
