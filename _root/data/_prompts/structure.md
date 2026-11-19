# Veratree Repository Structure

## Overview

The repository root is referred to as `root/` throughout this document. The structure is **fractal** — the same folder pattern repeats at both the root level and inside each product. Everything is a product, including the platform itself.

---

## Root Layout

```
root/
├── product.json           — root product manifest
├── _root/                   — platform infrastructure (app, data, platform, ops)
│   ├── app/               — FastAPI application container
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── ...
│   ├── data/              — root-level data (SQL, prompts, docs)
│   │   ├── _postgres/     — system-level SQL (init.sql, seed data)
│   │   └── _prompts/      — shared engineering documentation
│   ├── platform/          — Docker Compose, Nginx
│   │   ├── _compose/      — Docker Compose files and .env
│   │   ├── _nginx/        — Nginx configs
│   │   └── up.sh          — start command: bash _root/platform/up.sh up -d
│   └── ops/               — deploy scripts (sync.sh)
├── finance/               — example product
└── product/               — example product
```

---

## The Four Layers

The repository is organized into four standard layers at the root level:

| Layer | Folder | Purpose |
|-------|--------|---------|
| Foundation | `_root/platform` | Docker Compose, Nginx reverse proxy |
| Data | `_root/data` | SQL schemas, seed data, prompts |
| App | `_root/app` | FastAPI application container |
| Ops | `_root/ops` | Deploy scripts (sync.sh) |

---

## The Fractal Pattern

Every product — including the root itself — follows this lean structure. The pattern repeats at every level: a product can contain sub-products, and those sub-products follow the same shape.

```
<product>/
├── product.json           — manifest: name, status, capabilities
├── _app/                  — standard: FastAPI routes
│   ├── __init__.py        — aggregates all feature routers
│   └── <feature>/
│       ├── __init__.py    — feature router with prefix
│       └── <endpoint>.py  — route handlers
├── _data/                 — standard: data layer
│   └── _postgres/         — standard: SQL and seed data
│       ├── init.sql       — schema DDL, run by bootstrap at startup
│       └── <product>/     — Hive-partitioned reference data
│           └── <schema>/
│               └── <table>/
│                   └── year=YYYY/month=MM/day=DD/
│                       └── data.parquet
└── <sub-product>/         — optional: nested product with its own product.json
    ├── product.json
    ├── _app/
    └── _data/
```

**Example — attendance product and its powerschool sub-product:**
```
attendance/
├── product.json
├── _app/                  — pipeline orchestration, contacts, analytics
├── _data/
│   └── _postgres/
│       ├── init.sql       — core.* and analytics.* schemas
│       └── attendance/core/  — reference data parquets (schools, sessions, etc.)
└── powerschool/           — sub-product: PowerSchool SIS adapter
    ├── product.json
    ├── _app/              — pull, stage, transform
    └── _data/
        ├── _postgres/
        │   └── init.sql   — powerschool.* staging schema
        └── powerschool/   — incremental parquets written by pipeline
```

---

## Underscore Convention

At the **root level**, platform infrastructure lives in `_root/`. Its four sub-folders (`app/`, `data/`, `platform/`, `ops/`) do not use underscores because they are inside `_root/` — the underscore prefix on `_root/` itself marks the entire folder as platform-owned and not a product.

At the **product level**, standard reserved slots keep their underscores: `_app/`, `_data/`, `_postgres/`.

| Prefix | Meaning | Examples |
|--------|---------|---------|
| `_name` | **Standard** — reserved slot, same purpose wherever it appears; skipped by bootstrap product discovery | `_root` (root), `_app`, `_data`, `_postgres` (product level) |
| `name`  | **Custom** — optional, product-specific, not assumed to exist | products, sub-products |

If a developer sees `_app` inside any product, they know exactly what's in it without looking.

---

## Products

Each product lives directly at `root/<name>/`. A fresh Veratree instance ships with no products. Products are added by dropping a conforming folder into `root/` — bootstrap and auto-discovery pick them up automatically on next startup.

```
root/
├── _root/               — platform infrastructure (not a product)
├── product/           — product department (attendance, notifications)
├── marketing/         — marketing department (veratree.os, acme.com)
└── finance/           — finance product
```

---

## The Platform Infrastructure

`_root/` is the platform infrastructure folder — bootstrap skips it because the underscore prefix marks it as non-product. It contains four sub-folders:

```
_root/
├── platform/
│   ├── up.sh                        — start command wrapper
│   ├── _compose/
│   │   ├── compose.yml              — Docker Compose (api, nginx, postgres, redis, worker, astro-*)
│   │   └── .env                     — platform environment variables
│   └── _nginx/
│       └── nginx.conf               — reverse proxy routing
├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── core.py             — settings composition + bootstrap entry point
│   ├── __init__.py
│   ├── _fastapi/           — FastAPI app factory, middleware, deps, entrypoint.sh
│   ├── _dramatiq/          — broker, tasks, task registry
│   ├── _apscheduler/       — scheduler
│   ├── _postgres/          — db engine, models, alembic migrations
│   ├── _jobs/              — job tracking (create_job, complete_job etc.)
│   ├── _prometheus/        — metrics
│   ├── _jsonlogger/        — structured logging
│   └── _studio/            — built-in chat interface (Claude / OpenAI)
├── data/
│   ├── _postgres/          — system-level SQL
│   └── _prompts/           — shared engineering documentation
└── ops/
    └── sync.sh             — deploy to EC2 via rsync
```

Start the stack with:
```bash
bash _root/platform/up.sh up -d
```

---

## How Products Are Wired Together

### API Routing — Auto-Discovery

`_fastapi/main.py` discovers product routers automatically at startup. No manual registration is needed. For each `product.json` with `"routes": true`, it imports `<name>._app` and mounts the router under `/<name>`:

```
GET /attendance/absences/
GET /notifications/send/
```

To add a new routed product, create `_app/__init__.py` with a `router` and set `"routes": true` in `product.json`. Nothing else needs to change.

### Bootstrap

`bootstrap.py` runs at API startup. It walks every product directory **recursively** — a product is initialized before its sub-products, so parent schemas exist before child staging tables are created. For each product it:
1. Loads `.env` from the product root into the environment
2. Checks for `_data/init.sql` — if present, runs it, then loads reference data based on `-- @seed:` comments in that file

### Astro Frontends

Each product with a web frontend runs its own Astro container. There is no shared Astro build. The Astro project lives at `<product>/_platform/_astro/`. Compose overrides are at `<product>/_platform/_compose/compose.override.yml`. The container is configured with a `base` path so all assets are scoped under `/<product>/`.

### product.json

Controls what bootstrap and auto-discovery do for each product:

```json
{
  "id": "<uuid>",
  "name": "acme",
  "description": "Example product",
  "status": "active",
  "capabilities": {
    "routes": true
  }
}
```

Bootstrap auto-detects database initialization by the presence of `_data/init.sql`. Seed order is declared with `-- @seed:` comments inside `init.sql`, not in `product.json`.

---

## Key Conventions

- **Platform infrastructure** lives in `_root/` — bootstrap skips `_root/` during product discovery because of the underscore prefix
- **Product-level standard slots** (`_app`, `_data`, `_postgres`) — keep underscore prefix; same purpose wherever they appear; bootstrap skips them during product discovery
- **No underscore** = custom or optional sub-products
- **File ownership** — the API container runs as root. If Docker writes files to bind-mounted directories with root ownership, fix with `sudo chown -R $(whoami):$(whoami) .` from the repo root
- **Endpoint paths** use hyphens (`/line-items`, `/daily-summary`)
- **Query parameters and JSON body fields** use snake_case (`customer_id`, `start_date`)
- **Env vars** are loaded lazily (inside functions, not at module import time) so bootstrap's `.env` loading takes effect before product code reads them
- **Seed order** is declared with `-- @seed:` comments in `init.sql`; parent tables before child tables; parent product is always initialized before its sub-products
- **Shared prompts** live at `root/_root/data/_prompts/`
