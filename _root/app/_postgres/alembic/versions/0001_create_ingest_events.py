"""create ingest_events"""

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401
from sqlalchemy.dialects import postgresql as psql

revision = "0001_create_ingest_events"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create enum only if missing (idempotent)
    op.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'job_status') THEN
        CREATE TYPE job_status AS ENUM ('queued','processing','done','error');
      END IF;
    END$$;
    """)

    # Prevent SQLAlchemy from trying to create it again during table DDL
    job_status = psql.ENUM(
        'queued', 'processing', 'done', 'error',
        name='job_status',
        create_type=False
    )

    op.create_table(
        'ingest_events',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True),
        sa.Column('message_id', psql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('request_id', sa.String(length=64), nullable=True),
        sa.Column('payload', psql.JSONB, nullable=False),
        sa.Column('status', job_status, nullable=False, server_default='queued'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('enqueued_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('finished_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index('idx_ingest_events_enqueued_at', 'ingest_events', ['enqueued_at'], unique=False)
    op.create_index('idx_ingest_events_status_enqueued_at', 'ingest_events', ['status','enqueued_at'], unique=False)

def downgrade() -> None:
    op.drop_index('idx_ingest_events_status_enqueued_at', table_name='ingest_events')
    op.drop_index('idx_ingest_events_enqueued_at', table_name='ingest_events')
    op.drop_table('ingest_events')
    op.execute("DROP TYPE IF EXISTS job_status")
