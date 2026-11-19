# Adding an Endpoint

## Overview

Endpoints live inside a product's `_app/` folder, organized by feature. Each feature gets its own sub-folder with an `__init__.py` (router wiring) and one or more route files.

---

## Folder Pattern

```
<product>/_app/
└── <feature>/
    ├── __init__.py       — sub-router with prefix
    ├── routes.py         — route handlers (or split into named files)
    └── utils.py          — shared helpers (optional)
```

When a feature has many endpoints, split by logical group rather than putting everything in `routes.py`:

```
└── <feature>/
    ├── __init__.py
    ├── utils.py
    ├── list.py           — GET /
    ├── detail.py         — GET /{id}
    └── sessions.py       — GET /{id}/sessions + PATCH /{id}/sessions/{sid}
```

---

## Step-by-Step

### 1. Create the feature folder

```bash
mkdir -p <product>/_app/<feature>
```

### 2. Create `__init__.py`

```python
from fastapi import APIRouter
from .routes import router as routes_router

router = APIRouter(prefix="/<feature>", tags=["<product>-<feature>"])
router.include_router(routes_router)

__all__ = ["router"]
```

### 3. Create the route file

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from _app._postgres import get_session

router = APIRouter()


class MyResponse(BaseModel):
    id: int
    name: str


@router.get("/", response_model=list[MyResponse])
async def list_items(db: AsyncSession = Depends(get_session)):
    result = await db.execute(text("SELECT id, name FROM <product>.<table> ORDER BY name"))
    return [MyResponse(**dict(row._mapping)) for row in result]
```

### 4. Wire into `_app/__init__.py`

```python
from fastapi import APIRouter
from .<feature> import router as <feature>_router

router = APIRouter()
router.include_router(<feature>_router)
```

### 5. Restart the API

```bash
bash _root/platform/up.sh restart api
```

---

## Naming Conventions

- **URL path segments** — hyphens: `/line-items`, `/daily-summary`, `/reset-week`
- **Query parameters** — snake_case: `?customer_id=1`
- **JSON body fields** — snake_case: `{ "customer_id": 1 }`
- **Python file names** — snake_case: `reset_week.py` (hyphens are not valid in Python filenames)
- **Router tags** — `"<product>-<feature>"`: `"billing-invoices"`

---

## Required Query Parameters

Use `Query(...)` with `...` (Ellipsis) to make a query parameter required:

```python
from fastapi import Query

@router.get("/")
async def get_items(customer_id: int = Query(...)):
    ...
```

Omitting the parameter returns a 422 automatically.

---

## Cross-Product Calls

To call another product's endpoint from within a route, use `httpx` — not direct imports:

```python
import httpx
import os

def _api_base() -> str:
    return os.getenv("INTERNAL_API_URL", "http://localhost:8000")

@router.get("/summary")
async def get_summary():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{_api_base()}/other-product/resource/", timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Upstream error")
    return resp.json()
```

---

## Checklist

- [ ] Feature folder created under `<product>/_app/`
- [ ] `__init__.py` with correct prefix and tag
- [ ] Route file(s) with Pydantic response models
- [ ] Router wired into `_app/__init__.py`
- [ ] URL paths use hyphens
- [ ] Query params and body fields use snake_case
- [ ] Env vars read lazily (inside functions)
- [ ] No direct imports from other products
- [ ] API restarted and endpoint tested
