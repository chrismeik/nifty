"""
APScheduler engine — autodiscovers and registers scheduled jobs from products.

Each product that needs scheduled jobs defines _app/schedule.py with a
register_jobs(scheduler) function. This module finds and calls them all at startup.
"""

import json
import importlib
import logging
import sys
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler

log = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

_PRODUCTS_DIR = Path("/root-product")


def _register_product_schedules() -> int:
    count = 0
    for manifest_path in sorted(_PRODUCTS_DIR.rglob("product.json")):
        product_dir = manifest_path.parent
        if product_dir.name.startswith(("_", ".")):
            continue
        schedule_path = product_dir / "_app" / "schedule.py"
        if not schedule_path.exists():
            continue
        parent = str(product_dir.parent)
        if parent not in sys.path:
            sys.path.insert(0, parent)
        name = json.loads(manifest_path.read_text()).get("name", product_dir.name)
        module = importlib.import_module(f"{name}._app.schedule")
        module.register_jobs(scheduler)
        count += 1
        log.info("scheduler: registered jobs from %s._app.schedule", name)
    return count


def start_scheduler() -> None:
    count = _register_product_schedules()
    scheduler.start()
    log.info("scheduler: started with %d product schedule(s)", count)


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    log.info("scheduler: stopped")
