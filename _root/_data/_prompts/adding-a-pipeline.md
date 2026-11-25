# Adding a Pipeline

## Overview

A pipeline is a sub-product of type `"pipeline"` that runs a multi-step background job on a schedule or via HTTP trigger. Each pipeline has three layers:

- **`pipeline.py`** — async orchestrator that runs all steps in sequence and manages the job record
- **`worker.py`** — Dramatiq actor that bridges the sync worker process to the async pipeline
- **`routes.py`** — HTTP trigger that enqueues the worker immediately

The worker is discovered and registered automatically at startup — no manual registration needed.

---

## Folder Structure

```
product/<parent>/<name>/
├── product.json
├── _data/
│   └── _postgres/
│       └── init.sql              — schema and tables owned by this pipeline
└── _app/
    ├── __init__.py           — mounts trigger router (and any task routers)
    ├── pipeline.py           — async orchestrator
    ├── routes.py             — POST /run HTTP trigger
    ├── worker.py             — Dramatiq actor
    └── tasks/
        ├── __init__.py
        └── <step>.py         — one file per pipeline step
```

---

## Step-by-Step

### 1. Create `product.json`

```json
{
  "id": "<uuid>",
  "name": "<name>",
  "type": "pipeline",
  "description": "<what this pipeline does>",
  "status": "active",
  "parents": ["<parent-product-uuid>"],
  "children": [
    {
      "id": "<uuid>",
      "name": "tasks",
      "type": "tasks",
      "description": "Individual pipeline tasks",
      "status": "active",
      "children": []
    }
  ],
  "dependencies": []
}
```

### 2. Create `_data/_postgres/init.sql`

```sql
-- @db: acme

-- =============================================================================
-- SCHEMA: <name>
-- Tables owned by the <name> pipeline.
-- =============================================================================

-- <product id="<uuid>">
CREATE SCHEMA IF NOT EXISTS <name>;
-- </product>
```

### 3. Create `_app/pipeline.py`

The orchestrator. Pure async — no Dramatiq imports. Calls `check_already_done` for idempotency, creates a job record, runs each step via `update_job_step`, then calls `complete_job` or `fail_job`.

```python
"""
<Name> pipeline orchestrator.
"""

import logging
from datetime import date

from _app._jobs import check_already_done, create_job, update_job_step, complete_job, fail_job

log = logging.getLogger(__name__)

_PRODUCT  = "acme"
_JOB_TYPE = "<name>_pipeline"


async def run_<name>_pipeline(school_id: int, target_date: date) -> None:
    scope = str(school_id)

    if await check_already_done(_PRODUCT, _JOB_TYPE, target_date, scope=scope):
        return

    job_id = await create_job(_PRODUCT, _JOB_TYPE, target_date, scope=scope)

    try:
        # Step 1 — <description>
        meta = await step_one(school_id, target_date)
        await update_job_step(job_id, "step1_<name>", meta)

        # Step N — ...

        await complete_job(job_id)

    except Exception as exc:
        log.exception("<name> pipeline failed for school=%s on %s", school_id, target_date)
        await fail_job(job_id, str(exc))
        raise
```

### 4. Create `_app/worker.py`

The Dramatiq actor. Handles the sync/async bridge — always disposes the engine before calling `asyncio.run()`.

```python
"""
Dramatiq actor for the <name> pipeline.
Enqueued by the HTTP trigger endpoint or the APScheduler daily job.
"""

import asyncio
import logging
from datetime import date

import dramatiq

from _app._dramatiq import redis_broker  # noqa: F401 — registers the Dramatiq broker

log = logging.getLogger(__name__)


@dramatiq.actor(queue_name="default")
def run_<name>_task(school_id: int, target_date_iso: str) -> None:
    from _app._postgres import engine
    from <name>._app.pipeline import run_<name>_pipeline

    target_date = date.fromisoformat(target_date_iso)
    log.info("<name> pipeline starting: school=%s date=%s", school_id, target_date)

    async def _run():
        await engine.dispose()
        await run_<name>_pipeline(school_id, target_date)

    asyncio.run(_run())
    log.info("<name> pipeline complete: school=%s date=%s", school_id, target_date)
```

### 5. Create `_app/routes.py`

HTTP trigger. Always enqueues — never runs inline.

```python
"""
HTTP trigger for the <name> pipeline.
"""

from datetime import date, datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class PipelineRunRequest(BaseModel):
    school_id: int
    target_date: date | None = None


class PipelineRunResponse(BaseModel):
    queued: bool
    school_id: int
    target_date: date


@router.post("/run", response_model=PipelineRunResponse)
async def trigger_pipeline(request: PipelineRunRequest) -> PipelineRunResponse:
    from <name>._app.worker import run_<name>_task

    target_date = request.target_date or datetime.now(timezone.utc).date()
    run_<name>_task.send(request.school_id, target_date.isoformat())

    return PipelineRunResponse(
        queued=True,
        school_id=request.school_id,
        target_date=target_date,
    )
```

### 6. Create `_app/__init__.py`

```python
from fastapi import APIRouter
from .routes import router as trigger_router

router = APIRouter()
router.include_router(trigger_router)

__all__ = ["router"]
```

### 7. Create `_app/tasks/__init__.py`

Empty file — just marks the directory as a package.

### 8. Schedule it (if needed)

Add a `schedules` key to `product.json`. Each entry declares a cron job against a Dramatiq actor in `worker.py`:

```json
"schedules": [
  {"id": "pull",    "actor": "run_<name>_task", "cron": "* * * * *"},
  {"id": "compact", "actor": "run_<name>_compact_task", "cron": "5 * * * *"}
]
```

Fields: `id` (unique within this product), `actor` (name of the actor in `_app/worker.py`), `cron` (5-field UTC) or `interval_seconds`. Optional `args` array for fixed arguments.

The scheduler calls `actor.send` — the job always runs in the worker process, never in the API. `GET /platform/schedules` lists all registered jobs and their next run times.

For anything a cron expression can't cover (dynamic intervals, conditional scheduling), use `_app/schedule.py` with a `register_jobs(scheduler)` function instead.

**If your pipeline needs its own queue** (to isolate it from other work), declare `queue_name` on the actor and add a worker service to `<product>/_platform/_compose/compose.override.yml`:

```python
# worker.py
@dramatiq.actor(queue_name="feeds")
def run_<name>_task(...):
    ...
```

```yaml
# compose.override.yml
services:
  worker-feeds:
    image: fastapi-api
    command: dramatiq _app._dramatiq.tasks _app._dramatiq.task_registry --processes 1 --threads 8 --queues feeds
    volumes:
      - ../../_root/_app:/_app
      - ../../../:/root-product
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_BROKER_URL=${REDIS_BROKER_URL}
      - REDIS_CACHE_URL=${REDIS_CACHE_URL}
      - PYTHONPATH=/:/root-product
```

`up.sh` autodiscovers and merges all `compose.override.yml` files — no changes to `_root` needed.

---

## Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Pipeline folder name | lowercase, no hyphens | `raffle`, `notify` |
| Dramatiq actor | `run_<name>_task` | `run_raffle_task`, `run_notify_task` |
| Pipeline entry point | `run_<name>_pipeline` | `run_raffle_pipeline` |
| `_JOB_TYPE` constant | `"<name>_pipeline"` | `"raffle_pipeline"` |
| Step keys in metadata | `step<N>_<description>` | `step1_pull`, `step4_absences` |
| Task files | one file per logical step | `absences.py`, `contacts.py` |

---

## How Auto-Discovery Works

`task_registry.py` walks every `product.json` under `/root-product` at worker startup. For any directory that contains `_app/worker.py`, it adds the directory's ancestors to `sys.path` and imports `<name>._app.worker`. The `@dramatiq.actor` decorator registers the actor when the module is imported — no manual step required.

This means dropping a new pipeline folder with a `product.json` and `_app/worker.py` is sufficient for the worker to start consuming its messages on next restart.

---

## The pipeline.py / worker.py Split

- **`pipeline.py`** owns *what* happens — pure async business logic, no queue dependencies, directly testable
- **`worker.py`** owns *how it gets invoked* — Dramatiq actor, sync/async bridge, nothing else

Do not put business logic in `worker.py`. Do not import Dramatiq in `pipeline.py`.

---

## Each Step's Meta Dict

Every task function returns a `(result, meta)` tuple. The `meta` dict is passed to `update_job_step`, which merges it into `platform.jobs.metadata` under the step key and automatically adds `completed_at`. Keep meta flat and informative — counts and IDs, not full records.

```python
meta = {
    "school_id":    school_id,
    "absent_count": len(student_ids),
    "student_ids":  student_ids,
}
return student_ids, meta
```

The full `metadata` column after a successful run looks like:

```json
{
  "step1_pull":    { "completed_at": "...", "source": "api", "students_count": 312, ... },
  "step2_stage":   { "completed_at": "...", "students_staged": 312, ... },
  "step3_transform": { "completed_at": "...", "attendance_events_written": 3, ... }
}
```

---

## Checklist

- [ ] `product.json` with type `"pipeline"`, correct parent UUID, and new UUIDs for each node
- [ ] `_data/_postgres/init.sql` starts with `-- @db: acme` and creates the pipeline's schema
- [ ] `pipeline.py` — async, no Dramatiq imports, calls `check_already_done` first
- [ ] `worker.py` — actor named `run_<name>_task`, imports pipeline inside `_run()`, calls `engine.dispose()` before `asyncio.run()`
- [ ] `routes.py` — imports worker inside the route handler (not at module level)
- [ ] `_app/__init__.py` — mounts trigger router
- [ ] `_app/tasks/__init__.py` — empty, present
- [ ] Dramatiq actor name is unique across all pipelines (`run_<name>_task`)
- [ ] `schedules` key in `product.json` if cron-driven (or `_app/schedule.py` for dynamic scheduling)
- [ ] Custom queue declared on actor and in `compose.override.yml` if isolation needed
- [ ] Worker and API restarted to pick up new actor
