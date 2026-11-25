# _data Folders — Seed Data & Schema Initialization

## The Rule

Seed data and schema definitions live at the **product level that owns them** — meaning the lowest level product that is the authoritative source for that data, and the highest level product where that data is broadly useful.

Ask: "Would every product under this umbrella ever need this data?" If yes, it belongs at the parent level. If it's specific to one product or pipeline, it belongs at that product's level.

## Structure

Every `_data/` folder contains:
- `init.sql` — creates the schemas and tables this product owns
- `<product-name>/<schema>/<table>/<partition>/data.parquet` — seed data

The subfolder under `_data/` must match the product's `"name"` field in `product.json`. Bootstrap uses this to locate the right parquet files.

```
product/acme/
├── _data/
│   ├── init.sql                          # creates core.* schema
│   └── acme/                             # matches "name": "acme"
│       └── core/
│           ├── local_education_agencies/
│           │   └── date=2026-10-07/data.parquet
│           ├── schools/
│           ├── sessions/
│           └── sis_configurations/
└── notify/
    └── _data/
        └── init.sql                      # creates analytics.* schema
                                          # no seed data — analytics tables start empty
```

## Ownership Examples

| Table | Owner | Reason |
|---|---|---|
| `core.local_education_agencies` | `acme` | Every product under acme needs district info |
| `core.schools` | `acme` | Every product under acme needs school info |
| `core.sessions` | `acme` | Academic year context used across products |
| `core.sis_configurations` | `acme` | Any product connecting to a SIS needs this |
| `core.students` | `acme` | Foundational — any product works with students |
| `core.contacts` | `acme` | Foundational — any product works with guardians |
| `core.student_school_attendance_events` | `acme` | Core Ed-Fi schema, shared across products |
| `analytics.student_absence_summary` | `notify` | Derived by the notify pipeline, specific to it |
| `analytics.notification_log` | `notify` | Produced by the notify pipeline |

## Partitioning

All Hive-partitioned data uses a single `date=YYYY-MM-DD` key (UTC):

```
<table>/date=2026-10-07/data.parquet
```

High-volume streams that need intra-day granularity add an `hour=` level:

```
<table>/date=2026-10-07/hour=14/part-<unix_ms>.parquet
```

The hour is zero-padded and UTC. Everything else — coin, school_id, etc. — stays a column, not a folder level. This keeps DuckDB range filters simple (`WHERE date BETWEEN '2026-10-01' AND '2026-10-31'`), avoids string-vs-int ambiguity on month/day values, and reduces folder depth.

---

## When a Product Has No _data Folder

Not every product needs one. `attendance` is a pure organizational folder — it groups attendance-related products but owns no schema of its own. No `_data/` folder needed.

## product.json Wiring

`product.json` has no data-related fields. The presence of `_data/init.sql` is enough — bootstrap detects it automatically and drives everything from there. No `capabilities` flag, no `seed_order` array.

## Declaring Seed Order in init.sql

Seed tables are declared as `-- @seed:` comments at the top of `init.sql`, in the order they should load:

```sql
-- @seed: core.local_education_agencies latest
-- @seed: core.schools latest
-- @seed: core.sessions latest
-- @seed: core.sis_configurations latest

CREATE SCHEMA IF NOT EXISTS core;
...
```

Order matters — `schools` has a FK to `local_education_agencies`, so LEAs must load first. Bootstrap reads these lines top-to-bottom and seeds in that sequence.

A product with schema but no seed data (like `notify`) just has `init.sql` with no `-- @seed:` lines.

## Seed Strategies

- `latest` — loads only the most recent partition. For reference/config data that is replaced, not appended (schools, sessions, SIS configs).
- `append` — loads all partitions in order, DO NOTHING on conflict. For immutable time-series (raw attendance events).
- `upsert` — loads all partitions in order, DO NOTHING on conflict. For slowly-changing records (students, contacts).

## Bootstrap Order

Bootstrap walks the product tree parent-first (depth-first, alphabetical). Schema is always created before child products run — so a child product can safely reference tables created by its parent's `init.sql`.

This means: **never define a table in a child's `init.sql` that a parent's `init.sql` depends on.**
