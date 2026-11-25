"""add idempotency and payload hash to ingest_events"""
from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401
revision = "0002_add_idempotency_and_hash"
down_revision = "0001_create_ingest_events"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("ingest_events", sa.Column("api_key", sa.String(length=64), nullable=True))
    op.add_column("ingest_events", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    op.add_column("ingest_events", sa.Column("payload_sha256", sa.String(length=64), nullable=False, server_default=""))
    op.create_index(
        "uq_ingest_events_api_key_idem",
        "ingest_events",
        ["api_key", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL")
    )
    # drop server_default
    op.alter_column("ingest_events", "payload_sha256", server_default=None)

def downgrade() -> None:
    op.drop_index("uq_ingest_events_api_key_idem", table_name="ingest_events")
    op.drop_column("ingest_events", "payload_sha256")
    op.drop_column("ingest_events", "idempotency_key")
    op.drop_column("ingest_events", "api_key")
