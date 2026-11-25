"""
APScheduler engine — autodiscovers and registers scheduled jobs from products.

Two registration paths:
  1. product.json "schedules" key — declarative cron/interval entries
  2. <slot>/schedule.py — imperative register_jobs(scheduler) for anything cron can't express
"""

import json
import importlib
import logging
import sys
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

log = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(
    timezone="UTC",
    job_defaults={
        "coalesce": True,
        "max_instances": 1,
        "misfire_grace_time": 30,
    },
)

_PRODUCTS_DIR = Path("/root-product")


def _ensure_sys_path(product_dir: Path) -> None:
    ancestor = product_dir.parent
    while True:
        p = str(ancestor)
        if p not in sys.path:
            sys.path.insert(0, p)
        if ancestor == _PRODUCTS_DIR or ancestor.parent == ancestor:
            break
        ancestor = ancestor.parent


def _register_manifest_schedules(product_dir: Path, manifest: dict, app_slot: str) -> int:
    entries = manifest.get("schedules", [])
    if not entries:
        return 0

    name = manifest.get("name", product_dir.name)
    registered = 0

    try:
        _ensure_sys_path(product_dir)
        worker_module = importlib.import_module(f"{name}.{app_slot}.worker")
    except Exception:
        log.exception("scheduler: failed to import %s.%s.worker — skipping schedules", name, app_slot)
        return 0

    for entry in entries:
        job_id = f"{name}.{entry['id']}"
        actor_name = entry.get("actor")
        args = entry.get("args", [])

        try:
            actor = getattr(worker_module, actor_name)
        except AttributeError:
            log.error("scheduler: actor %r not found in %s.%s.worker — skipping", actor_name, name, app_slot)
            continue

        try:
            if "cron" in entry:
                trigger = CronTrigger.from_crontab(entry["cron"], timezone="UTC")
            elif "interval_seconds" in entry:
                trigger = IntervalTrigger(seconds=entry["interval_seconds"])
            else:
                log.error("scheduler: job %r has no cron or interval_seconds — skipping", job_id)
                continue

            job = scheduler.add_job(
                actor.send,
                trigger,
                args=args,
                id=job_id,
                replace_existing=True,
            )
            # next_run_time only exists once the scheduler has started (APScheduler 3.x)
            log.info("scheduler: registered %s (actor=%s, next=%s)", job_id, actor_name, getattr(job, "next_run_time", "pending"))
            registered += 1

        except Exception:
            log.exception("scheduler: failed to register job %r — skipping", job_id)

    return registered


def _register_schedule_py(product_dir: Path, manifest: dict, app_slot: str) -> int:
    schedule_path = product_dir / app_slot / "schedule.py"
    if not schedule_path.exists():
        return 0

    name = manifest.get("name", product_dir.name)
    try:
        _ensure_sys_path(product_dir)
        module = importlib.import_module(f"{name}.{app_slot}.schedule")
        module.register_jobs(scheduler)
        log.info("scheduler: registered jobs from %s.%s.schedule", name, app_slot)
        return 1
    except Exception:
        log.exception("scheduler: failed to load %s.%s.schedule — skipping", name, app_slot)
        return 0


def _register_product_schedules() -> int:
    count = 0
    for manifest_path in sorted(_PRODUCTS_DIR.rglob("product.json")):
        product_dir = manifest_path.parent
        if product_dir.name.startswith(("_", ".")):
            continue
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            log.warning("scheduler: could not parse %s — skipping", manifest_path)
            continue

        app_slot = "_app" if (product_dir / "_app").is_dir() else "app"
        count += _register_manifest_schedules(product_dir, manifest, app_slot)
        count += _register_schedule_py(product_dir, manifest, app_slot)

    return count


def start_scheduler() -> None:
    count = _register_product_schedules()
    scheduler.start()
    log.info("scheduler: started with %d job(s)", count)


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    log.info("scheduler: stopped")
