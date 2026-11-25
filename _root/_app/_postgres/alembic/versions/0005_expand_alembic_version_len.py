# alembic/versions/0005_expand_alembic_version_len.py
from alembic import op  # noqa: F401
revision = "0005_expand_alembic_version_len"
down_revision = "0004_add_idx_ingest_enqueued_at"  # <-- adjust if your head is different
branch_labels = None
depends_on = None

def upgrade():
    # Widen to 128 to allow long, descriptive revision ids.
    # This table typically has 1 row; the ALTER is very fast.
    with op.get_context().autocommit_block():
        op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)")

def downgrade():
    # Shrinking back to 32 may fail if any stored revision ids exceed 32 chars.
    # If you *must* support downgrade, this variant truncates to 32.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TABLE alembic_version "
            "ALTER COLUMN version_num TYPE VARCHAR(32) "
            "USING LEFT(version_num, 32)"
        )
