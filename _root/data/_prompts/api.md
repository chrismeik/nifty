# API Conventions

## Overview

The API is built with FastAPI. All product endpoints live inside their respective product folder and are chained together through a hierarchy of `APIRouter` instances. The shared FastAPI app lives in `app/_fastapi/`.

---

## Router Chaining

Routers stack from the inside out:

```
root router  (no prefix)
└── product router  (prefix="/billing")
    └── feature router  (prefix="/invoices")
        └── route handler  (path="/")
```

Result: `GET /billing/invoices/`

Each level has an `__init__.py` that wires sub-routers together:

```python
# billing/_app/invoices/__init__.py
from fastapi import APIRouter
from .routes import router as routes_router

router = APIRouter(prefix="/invoices", tags=["billing-invoices"])
router.include_router(routes_router)
```

```python
# billing/_app/__init__.py
from fastapi import APIRouter
from .invoices import router as invoices_router

router = APIRouter()
router.include_router(invoices_router)
```

---

## Route Files

- Each feature gets its own file or folder under `<product>/_app/<feature>/`
- Closely related endpoints (e.g., GET + PATCH on the same resource) can share a file
- Shared helpers (auth, formatting, status checks) go in `utils.py` within the feature folder

---

## Database Access

Two patterns exist — use whichever matches the existing code in that product:

**Session (dependency injection):**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from _app._postgres import get_session

@router.get("/")
async def my_endpoint(db: AsyncSession = Depends(get_session)):
    result = await db.execute(text("SELECT ..."))
```

**Engine (context manager):**
```python
from _app._postgres import engine

@router.get("/")
async def my_endpoint():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT ..."))
```

---

## Lazy Environment Variables

Always read environment variables inside functions, never at module level:

```python
# correct
def get_api_key() -> str:
    return os.getenv("MY_API_KEY", "")

# wrong — reads before bootstrap loads the .env
API_KEY = os.getenv("MY_API_KEY", "")
```

This is required because bootstrap loads per-product `.env` files at runtime, after modules are imported.

---

## Naming Conventions

- **URL path segments** — hyphens: `/line-items`, `/reset-week`, `/daily-summary`
- **Query parameters** — snake_case: `?customer_id=1`, `?start_date=2026-01-01`
- **JSON body fields** — snake_case: `{ "customer_id": 1, "line_items": [] }`
- **Python identifiers** — snake_case throughout

---

## Response Models

Use Pydantic `BaseModel` for all request and response bodies. Define models in the same file as the route unless shared across multiple routes, in which case move them to a `models.py` in the feature folder.

---

## Datetime

All datetimes must be UTC:
```python
from datetime import datetime, timezone
datetime.now(timezone.utc)   # correct
datetime.utcnow()            # wrong — deprecated, returns naive datetime
datetime.now()               # wrong — returns local time
```

Postgres timestamp columns must be `TIMESTAMP WITH TIME ZONE`.

---

## Cross-Product Communication

Products communicate via HTTP, not direct Python imports. Use `httpx` to call another product's endpoint:

```python
async with httpx.AsyncClient() as client:
    resp = await client.get("http://localhost:8000/other-product/resource/")
```

This keeps product teams decoupled — each product is only responsible for its own API contract.
