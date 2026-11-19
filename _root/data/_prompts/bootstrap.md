# Bootstrap

## Overview

`app/core.py` exposes `bootstrap()`, which is called automatically at API startup via FastAPI's lifespan hook. It delegates to `app/_postgres/bootstrap.py`, which is the single entry point for initializing all products and sub-products — database schemas and reference data.

---

## Execution Order

1. SQLAlchemy model tables are created first (`Base.metadata.create_all`)
2. The root product is initialized
3. Each top-level product in `root/` is initialized in alphabetical order
4. After each product is initialized, bootstrap recurses into its sub-products (directories containing their own `product.json`), also in alphabetical order
5. Parent products are always fully initialized before their sub-products

---

## Per-Product Initialization (`_init_product`)

For each directory that contains a `product.json`:

1. **Load `.env`** — loaded using `load_dotenv(override=False)`. Existing environment variables are never overwritten.
2. **Check for `_data/init.sql`** — if present, runs `_init_postgres()`, then `_load_reference_data()` based on `-- @seed:` comments in the file
3. **Recurse** → checks all non-underscore subdirectories for their own `product.json` and initializes them

Bootstrap auto-detects database initialization by the presence of `_data/init.sql` — no `capabilities` flag in `product.json` is needed.

---

## Postgres Initialization (`_init_postgres`)

Reads `_data/init.sql` (product-level `_data/` keeps its underscore) and executes each statement split on `;`. Use this file for:
- `CREATE SCHEMA IF NOT EXISTS`
- `CREATE TABLE IF NOT EXISTS`
- Indexes and constraints

All DDL must be idempotent (`IF NOT EXISTS`) so re-running bootstrap on an existing database is always safe.

---

## Reference Data Loading (`_load_reference_data`)

Reads parquet files from the unified Hive layout:

```
_data/_postgres/<product_name>/<schema>/<table>/year=YYYY/month=MM/day=DD/data.parquet
```

Seed tables are declared as `-- @seed:` comments at the top of `init.sql`, in the order they should load:

```sql
-- @seed: core.local_education_agencies latest
-- @seed: core.schools latest
-- @seed: core.sessions latest
-- @seed: core.sis_configurations latest

CREATE SCHEMA IF NOT EXISTS core;
...
```

Bootstrap reads these lines top-to-bottom and seeds in that sequence.

### Strategies

| Strategy | Which partitions | Use for |
|---|---|---|
| `latest` | Most recent date partition only | Config/reference data — schools, sessions, SIS config |
| `append` | All partitions, chronological order | Immutable time-series — attendance events, notification logs |
| `upsert` | All partitions, chronological order | Slowly-changing records — students, contacts |

All strategies use `ON CONFLICT DO NOTHING` — re-running bootstrap never duplicates rows.

### Key rules
- If no `-- @seed:` lines are present, nothing is loaded — prevents bootstrap from accidentally replaying pipeline-managed data
- Entries must be in FK order — parent tables before child tables
- Reference data and incremental pipeline data share the same `_data/` folder; `-- @seed:` comments are the explicit declaration of what bootstrap owns

---

## Sub-Products

Bootstrap automatically discovers sub-products. Any subdirectory (without an underscore prefix) that contains a `product.json` is treated as a sub-product and initialized after its parent.

**Example:** `acme/` initializes first (creates `core.*` schemas), then `acme/powerschool/` initializes (creates `powerschool.*` staging schema).

There is no depth limit — sub-products can contain their own sub-products.

---

## Router Auto-Discovery

Router wiring is **not** bootstrap's responsibility — it belongs to `_fastapi/main.py`. At startup, `main.py` iterates `root/`, finds every `product.json` with `"routes": true`, imports `<name>._app`, and mounts the router under `/<name>`. No manual registration is needed.

---

## Key Behaviors

- `.env` uses `override=False` — environment always wins over file values
- Missing optional files (`init.sql`, missing parquet partitions) are silently skipped
- All database operations use the shared async SQLAlchemy engine from `_app._postgres`
- Bootstrap is **not** the place to run one-time provisioning scripts — those are run manually by developers
