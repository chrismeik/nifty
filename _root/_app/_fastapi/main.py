import json
import sys
import importlib
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import redis.asyncio as redis

from _app.core import settings, bootstrap
from _app._apscheduler.scheduler import start_scheduler, stop_scheduler, scheduler
from _app._studio import router as studio_router
import warnings
from pydantic import PydanticDeprecatedSince20

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

PRODUCTS_DIR = Path("/root-product")


def _load_product_routers(app: FastAPI):
    _walk_routers(PRODUCTS_DIR, app)

def _walk_routers(base_dir: Path, app: FastAPI):
    for product_dir in sorted(base_dir.iterdir()):
        if not product_dir.is_dir() or product_dir.name.startswith(("_", ".")):
            continue
        manifest_path = product_dir / "product.json"
        if not manifest_path.exists():
            continue
        app_slot = "_app" if (product_dir / "_app" / "__init__.py").exists() else "app" if (product_dir / "app" / "__init__.py").exists() else None
        if app_slot:
            manifest = json.loads(manifest_path.read_text())
            name = manifest["name"]
            parent = str(product_dir.parent)
            if parent not in sys.path:
                sys.path.insert(0, parent)
            module = importlib.import_module(f"{name}.{app_slot}")
            product_router = APIRouter(prefix=f"/{name}", tags=[name])
            product_router.include_router(module.router)
            app.include_router(product_router)
        _walk_routers(product_dir, app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bootstrap()
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


app = FastAPI(
    title="FastAPI Dramatiq Ingestion",
    lifespan=lifespan
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.include_router(studio_router, prefix="/studio", tags=["studio"])
_load_product_routers(app)

_raw_origins = getattr(settings, "ALLOWED_ORIGINS", "")
origins = [o.strip() for o in _raw_origins.split(",") if o.strip()] if _raw_origins else [
    "http://localhost",
    "http://localhost:4321",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/platform/schedules", tags=["platform"])
async def list_schedules():
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "trigger": str(job.trigger),
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        })
    return {"jobs": jobs}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/readyz")
async def readyz():
    broker_ok = cache_ok = False
    rb = rc = None
    try:
        rb = redis.from_url(settings.redis_broker_url)
        await rb.ping()
        broker_ok = True
    except Exception:
        pass
    finally:
        if rb is not None:
            await rb.close()

    try:
        rc = redis.from_url(settings.redis_cache_url)
        await rc.ping()
        cache_ok = True
    except Exception:
        pass
    finally:
        if rc is not None:
            await rc.close()

    status = "ready" if (broker_ok and cache_ok) else "degraded"
    return {"status": status, "redis_broker": broker_ok, "redis_cache": cache_ok}