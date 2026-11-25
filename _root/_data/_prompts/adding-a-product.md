# Adding a Product

## Overview

A product is a self-contained module with its own API routes, database schema, seed data, and optionally a web frontend. Bootstrap and auto-discovery pick up any product dropped into `root/` automatically on next startup.

---

## Step-by-Step

### 1. Create the folder structure

```bash
mkdir -p <name>/_app
mkdir -p <name>/_data/_postgres
```

Only create a frontend if this product needs a web frontend.

### 2. Create `product.json`

```json
{
  "name": "<name>",
  "description": "",
  "status": "active",
  "capabilities": {
    "routes": true
  }
}
```

### 3. Create `_app/__init__.py`

```python
from fastapi import APIRouter

router = APIRouter()

__all__ = ["router"]
```

As you add features, import their routers here:

```python
from fastapi import APIRouter
from .invoices import router as invoices_router

router = APIRouter()
router.include_router(invoices_router)

__all__ = ["router"]
```

### 4. Add `.env` and `.gitignore` at the product root

```bash
touch <name>/.env
echo ".env" > <name>/.gitignore
```

Product-scoped secrets go in `.env`. Bootstrap loads it at startup with `override=False` — existing environment variables are never overwritten.

### 5. Add a database schema (if needed)

Create `<name>/_data/_postgres/init.sql`:

```sql
CREATE SCHEMA IF NOT EXISTS <name>;

CREATE TABLE IF NOT EXISTS <name>.<table> (
    id         SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)
```

Bootstrap auto-detects the presence of `_data/init.sql` — no `capabilities` flag needed in `product.json`.

### 6. Add reference data (if needed)

Generate parquet files and place them at:
```
<name>/_data/_postgres/<name>/<schema>/<table>/date=YYYY-MM-DD/data.parquet
```

Declare seed order with `-- @seed:` comments at the top of `init.sql`:
```sql
-- @seed: <schema>.<parent_table> latest
-- @seed: <schema>.<child_table> latest

CREATE SCHEMA IF NOT EXISTS <name>;
...
```

Strategies: `latest` (most recent partition — reference data), `append` (all partitions — immutable time-series), `upsert` (all partitions — slowly-changing records). Parent tables must appear before child tables.

### 7. Add a sub-product (if needed)

Sub-products follow the exact same pattern as top-level products. Create a subdirectory without an underscore prefix — bootstrap discovers it automatically:

```bash
mkdir -p <name>/<sub-name>/_app
mkdir -p <name>/<sub-name>/_data/_postgres
```

Create `<name>/<sub-name>/product.json` with its own capabilities. The parent product is always initialized before the sub-product.

### 8. Add an Astro frontend (if needed)

Create `<name>/_platform/_astro/` with the Astro project files, and `<name>/_platform/_compose/compose.override.yml` for compose overrides:

```
<name>/_platform/
├── _astro/
│   ├── Dockerfile
│   ├── astro.config.mjs
│   └── src/
└── _compose/
    └── compose.override.yml
```

Set `astro.config.mjs` base and server:

```js
base: '/<name>',
server: { host: true, port: <unique_port> }
```

Add the service to `_root/_platform/_compose/compose.yml` pointing the build context and bind mount at `<name>/_platform/_astro`, and add a location block to `_root/_platform/_nginx/nginx.conf`.

### 9. Restart the API

```bash
bash _root/_platform/up.sh restart api
```

Auto-discovery in `main.py` finds the new `_app` module via `product.json` — no manual router registration needed.

---

## Checklist

- [ ] `product.json` present with correct name and capabilities
- [ ] `_app/__init__.py` with a `router` (if `routes: true`)
- [ ] `.env` and `.gitignore` at product root
- [ ] `_data/_postgres/init.sql` written idempotently (if database needed)
- [ ] `-- @seed:` comments in `init.sql` declare seed tables in FK order (if reference data needed)
- [ ] Reference parquets at `_data/_postgres/<name>/<schema>/<table>/date=YYYY-MM-DD/data.parquet` (if reference data needed)
- [ ] Sub-products created as plain subdirectories with their own `product.json` (if needed)
- [ ] Astro container added to compose and nginx (if web frontend needed)
- [ ] API restarted and bootstrap log confirms initialization
