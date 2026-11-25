from alembic import op  # noqa: F401
revision = "0004_add_idx_ingest_enqueued_at"
down_revision = "0003_unique_idem_idx"
branch_labels = None
depends_on = None

def upgrade():
    with op.get_context().autocommit_block():
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ingest_enqueued_at "
            "ON ingest_events (enqueued_at)"
        )

def downgrade():
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_ingest_enqueued_at")
