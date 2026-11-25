# Veratree Repository Structure

## Overview

The repository root is referred to as `root/` throughout this document. The structure is **fractal** — the same folder pattern repeats at both the root level and inside each product. Everything is a product, including the platform itself.

---

## Root Layout

```
root/
├── product.json           — root product manifest
├── _root/                   — platform infrastructure (_app, _data, _platform, _ops)
│   ├── _app/              — FastAPI application container
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── ...
│   ├── _data/             — root-level data (SQL, prompts, docs)
│   │   ├── _postgres/     — system-level SQL (init.sql, seed data)
│   │   └── _prompts/      — shared engineering documentation
│   ├── _platform/         — Docker Compose, Nginx
│   │   ├── _compose/      — Docker Compose files and .env
│   │   ├── _nginx/        — Nginx configs
│   │   └── up.sh          — start command: bash _root/_platform/up.sh up -d
│   └── _ops/              — operations (_dataops, utils)
├── finance/               — example product
└── product/               — example product
```

---

## The Four Layers

The repository is organized into four standard layers at the root level:

| Layer | Folder | Purpose |
|-------|--------|---------|
| Foundation | `_root/_platform` | Docker Compose, Nginx reverse proxy |
| Data | `_root/_data` | SQL schemas, seed data, prompts |
| App | `_root/_app` | FastAPI application container |
| Ops | `_root/_ops` | Runtime data operations (`_dataops`) and host-side utilities |

---

## The Underscore Convention

A leading underscore on a folder means it was created from a template and is expected to follow that template's rules. Think of it as a contract: the folder has a defined shape, defined contents, and defined behavior. There is some wiggle room — enough to make it sensible to stay templated — but not so much that it becomes a free-form custom folder.

This applies at every fractal level:

- `_data/` — always contains templated subdirectories like `_postgres/`, `_duckdb/`, `_prompts/`. The processes inside are well-defined and repeatable.
- `_platform/` — always contains `_compose/` and `up.sh`. Also contains `_nginx/` if the product serves HTTP. The same shape appears in every product that has infrastructure.
- `_app/` — the FastAPI application layer in `_root`. Templated for the core system.

A folder **without** an underscore signals intentional flexibility. For example, a custom product might create an `app/` folder (no underscore) because its application layer has enough unique requirements that the template doesn't apply. Dropping the underscore is a deliberate signal: *this doesn't follow the template, and that's fine*.

The rule of thumb: if you're following the template closely enough that someone reading the folder name would know what to expect inside, keep the underscore. If you're diverging meaningfully, drop it.

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
│                   └── date=YYYY-MM-DD/
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

A leading underscore means the folder was created from a template and follows its rules. See the **The Underscore Convention** section above for the full explanation.

| Prefix | Meaning | Examples |
|--------|---------|---------|
| `_name` | **Templated** — defined shape, skipped by bootstrap product discovery | `_root`, `_app`, `_data`, `_platform`, `_postgres` |
| `name`  | **Custom** — product-specific, flexible | products, sub-products, custom `app/` |

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
├── _platform/
│   ├── up.sh                        — start command wrapper
│   ├── _compose/
│   │   ├── compose.yml              — Docker Compose (api, nginx, postgres, redis, worker, astro-*)
│   │   └── .env                     — platform environment variables
│   └── _nginx/
│       └── nginx.conf               — reverse proxy routing
├── _app/
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
├── _data/
│   ├── _postgres/          — system-level SQL
│   └── _prompts/           — shared engineering documentation
└── _ops/
    ├── _dataops/           — runtime data operations (e.g. _s3_copy: copy files to S3)
    └── utils/              — host-side utilities (sync_root.py copies _root into each project)
```

Start the stack with:
```bash
bash _root/_platform/up.sh up -d
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
  },
  "schedules": [
    {"id": "pull",    "actor": "run_pull_task",    "cron": "* * * * *"},
    {"id": "compact", "actor": "run_compact_task", "cron": "5 * * * *"}
  ]
}
```

`schedules` is optional. Each entry needs `id` (unique within the product), `actor` (a Dramatiq actor in `<slot>/worker.py`), and either `cron` (5-field UTC) or `interval_seconds`. Optional `args` array passes fixed arguments to the actor. The scheduler uses `actor.send` so jobs always run in the worker process, never in the API.

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
- **Shared prompts** live at `root/_root/_data/_prompts/`
