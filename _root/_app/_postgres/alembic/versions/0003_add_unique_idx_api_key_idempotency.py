"""add unique idx on (api_key, idempotency_key) when key is not null

Revision ID: 0003_unique_idem_idx
Revises: 0002_add_idempotency_and_hash
Create Date: 2025-08-17
"""
from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401
# revision identifiers, used by Alembic.
revision = "0003_unique_idem_idx"
down_revision = "0002_add_idempotency_and_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            "uq_ingest_api_key_idempotency",
            "ingest_events",
            ["api_key", "idempotency_key"],
            unique=True,
            postgresql_where=sa.text("idempotency_key IS NOT NULL"),
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(
            "uq_ingest_api_key_idempotency",
            table_name="ingest_events",
            postgresql_concurrently=True,
        )
