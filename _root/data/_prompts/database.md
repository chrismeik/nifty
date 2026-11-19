# Database Conventions

## Overview

Veratree uses PostgreSQL with async SQLAlchemy. Each product owns its own Postgres schema, keeping data cleanly separated. All database initialization happens through bootstrap at startup.

---

## Schema Per Product

Each product creates its own schema in `init.sql`:

```sql
CREATE SCHEMA IF NOT EXISTS billing;
```

All tables for that product live under that schema:

```sql
CREATE TABLE IF NOT EXISTS billing.invoices ( ... );
CREATE TABLE IF NOT EXISTS billing.line_items ( ... );
```

Never create tables in the `public` schema. Never write to another product's schema from within a product's own code.

Products with multiple data layers (e.g., raw staging + canonical + analytics) use multiple schemas within the same database, named to reflect their purpose.

---

## init.sql

Located at `_data/init.sql` inside each product (product-level `_data/` keeps its underscore). Rules:

- All statements must be idempotent (`IF NOT EXISTS`)
- Statements are split on `;` by bootstrap — do not use `;` inside function bodies or triggers
- Define tables in foreign key order (parent tables first)
- End the file without a trailing `;` on the last statement

Example:
```sql
CREATE SCHEMA IF NOT EXISTS billing;

CREATE TABLE IF NOT EXISTS billing.customers (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing.invoices (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES billing.customers(id),
    total       NUMERIC(10, 2) NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)
```

---

## Reference and Pipeline Data

All data — reference/config and incremental pipeline output — lives in the same Hive-partitioned layout:

```
_data/<product_name>/<schema>/<table>/year=YYYY/month=MM/day=DD/data.parquet
```

Seed tables are declared as `-- @seed:` comments at the top of `init.sql`. Each entry specifies a table name and loading strategy:

```sql
-- @seed: core.schools           latest
-- @seed: core.sessions          latest
-- @seed: powerschool.attendance append
```

| Strategy | Partitions loaded | `ON CONFLICT` | Use for |
|---|---|---|---|
| `latest` | Most recent only | `DO NOTHING` | Config/reference — schools, sessions |
| `append` | All, chronological | `DO NOTHING` | Immutable time-series — attendance |
| `upsert` | All, chronological | `DO NOTHING` | Slowly-changing — students, contacts |

To refresh reference data: write a new dated parquet. Bootstrap always picks up the latest partition.

Tables with no `-- @seed:` entry are pipeline-managed — bootstrap creates the schema but never touches the data.

---

## Datetime

- All timestamp columns must be `TIMESTAMP WITH TIME ZONE`
- `NOW()` in Postgres returns UTC when the column is timezone-aware
- In Python, always use `datetime.now(timezone.utc)` — never `datetime.utcnow()` or `datetime.now()`
- When serializing to string: `datetime.now(timezone.utc).isoformat()`

---

## Column Naming

- snake_case for all column names
- Primary keys: `id`
- Foreign keys: `<referenced_table_singular>_id` (e.g., `customer_id`, `invoice_id`)
- Timestamps: `created_at`, `modified_at`
- Boolean flags: `is_<state>` (e.g., `is_active`, `is_primary`)
- Soft delete: `is_active BOOLEAN NOT NULL DEFAULT true`

---

## Constraints

Use CHECK constraints for enumerated string values:

```sql
status TEXT NOT NULL CHECK (status IN ('pending', 'paid', 'cancelled'))
```

Use UNIQUE constraints to enforce business rules at the database level:

```sql
UNIQUE (customer_id, invoice_date)
```

---

## Querying

Use raw SQL via SQLAlchemy `text()` — no ORM models for product tables:

```python
from sqlalchemy import text

result = await db.execute(
    text("SELECT id, name FROM billing.customers WHERE is_active = true ORDER BY name"),
)
rows = result.fetchall()
```

Always use named bind parameters (`:param`) — never f-string user input into queries:

```python
# correct
await db.execute(text("SELECT * FROM billing.invoices WHERE id = :id"), {"id": invoice_id})

# wrong — SQL injection risk
await db.execute(text(f"SELECT * FROM billing.invoices WHERE id = {invoice_id}"))
```
