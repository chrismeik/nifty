import asyncio
import os
from _app._postgres.maintenance import prune_ingest_events

if __name__ == "__main__":
    days = int(os.getenv("RETENTION_DAYS", "30"))
    deleted = asyncio.run(prune_ingest_events(days=days))
    print(f"Deleted {deleted} old ingest_events (>{days} days)")
