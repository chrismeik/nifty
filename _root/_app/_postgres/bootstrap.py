import json
import pandas as pd
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from _app._postgres.db import engine
from _app._postgres.models import Base

ROOT_DIR = Path("/root-product")


async def init():
    # SQLAlchemy model tables — always first
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # System schema (platform, system tables) must exist before any product registration
    system_sql = ROOT_DIR / "_root" / "_data" / "_postgres" / "init.sql"
    if system_sql.exists():
        statements = [s.strip() for s in system_sql.read_text().split(";") if s.strip()]
        async with engine.begin() as conn:
            for stmt in statements:
                await conn.execute(text(stmt))

    # Pass 1: postgres product registration (no relationships yet)
    relationships: list[tuple[str, str, str]] = []
    await _init_product(ROOT_DIR, relationships)

    # Pass 2: register all relationships now that every product exists
    for source_id, target_id, kind in relationships:
        await _register_relationship(source_id, target_id, kind)

    print("✅ Bootstrap complete")


async def _init_product(product_dir: Path, relationships: list):
    manifest_path = product_dir / "product.json"
    if not manifest_path.exists():
        # The project home (e.g. veratree/bot) has no manifest of its own,
        # so start from the products in its subfolders.
        if product_dir == ROOT_DIR:
            for sub_dir in sorted(product_dir.iterdir()):
                if sub_dir.is_dir() and not sub_dir.name.startswith("."):
                    if (sub_dir / "product.json").exists():
                        await _init_product(sub_dir, relationships)
        return

    env_file = product_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)

    manifest = json.loads(manifest_path.read_text())
    name = manifest["name"]

    sql_file = product_dir / "_data" / "init.sql"
    if sql_file.exists():
        db_name, seed_order = _parse_seed_order(sql_file)
        await _init_postgres(product_dir, name)
        await _load_reference_data(product_dir, db_name, seed_order)

    await _register_product(manifest, relationships)

    # Recurse into sub-products — any subdirectory with its own product.json
    for sub_dir in sorted(product_dir.iterdir()):
        if sub_dir.is_dir() and not sub_dir.name.startswith("."):
            if (sub_dir / "product.json").exists():
                await _init_product(sub_dir, relationships)


def _parse_seed_order(sql_file: Path) -> tuple[str | None, list]:
    db_name = None
    seed_order = []
    for line in sql_file.read_text().splitlines():
        line = line.strip()
        if line.startswith("-- @db:"):
            db_name = line[len("-- @db:"):].strip()
        elif line.startswith("-- @seed:"):
            parts = line[len("-- @seed:"):].strip().split()
            if len(parts) >= 2:
                seed_order.append({"table": parts[0], "strategy": parts[1]})
            elif len(parts) == 1:
                seed_order.append({"table": parts[0], "strategy": "latest"})
    return db_name, seed_order


async def _init_postgres(product_dir: Path, name: str):
    sql_file = product_dir / "_data" / "init.sql"
    if not sql_file.exists():
        return
    statements = [s.strip() for s in sql_file.read_text().split(";") if s.strip()]
    async with engine.begin() as conn:
        for stmt in statements:
            await conn.execute(text(stmt))
    print(f"  ✅ Postgres initialized: {name}")


def _latest_partition(table_dir: Path) -> Path | None:
    """Return data.parquet from the most recent date=YYYY-MM-DD partition."""
    from datetime import date as date_type

    best_file: Path | None = None
    best_date: date_type | None = None

    for date_dir in table_dir.glob("date=*"):
        matches = list(date_dir.rglob("*.parquet"))
        if not matches:
            continue
        f = sorted(matches)[0]
        try:
            d = date_type.fromisoformat(date_dir.name.split("=", 1)[1])
        except (ValueError, IndexError):
            continue
        if best_date is None or d > best_date:
            best_date = d
            best_file = f

    return best_file


def _all_partitions(table_dir: Path) -> list[Path]:
    """
    Return all data.parquet files under table_dir in chronological order.
    Handles both flat (date=YYYY-MM-DD/data.parquet) and sub-partitioned
    (date=YYYY-MM-DD/school_id=NNN/data.parquet) layouts.
    ISO date=YYYY-MM-DD names ensure alphabetical == chronological sort.
    """
    return sorted(table_dir.rglob("*.parquet"))


async def _load_reference_data(product_dir: Path, db_name: str | None, seed_order: list | None = None):
    """
    Load reference/config data from _data/<db>/<schema>/<table>/<partition>/data.parquet.

    seed_order entries are objects: {"table": "schema.table", "strategy": "latest|append|upsert"}
    - latest: most recent partition only — for config/reference data (schools, sessions)
    - append: all partitions in order, DO NOTHING — for immutable time-series (attendance)
    - upsert: all partitions in order, DO NOTHING — for slowly-changing records (students)

    If db_name or seed_order is absent, nothing is loaded.
    """
    data_root = product_dir / "_data" / db_name if db_name else None
    if not data_root or not data_root.exists() or not seed_order:
        return

    for entry in seed_order:
        if isinstance(entry, str):
            table_key, strategy = entry, "latest"
        else:
            table_key = entry["table"]
            strategy = entry.get("strategy", "latest")

        if "." not in table_key:
            continue
        schema, table_name = table_key.split(".", 1)
        table_dir = data_root / schema / table_name
        if not table_dir.is_dir():
            continue

        if strategy == "latest":
            parquet_files = [f for f in [_latest_partition(table_dir)] if f]
        else:
            parquet_files = _all_partitions(table_dir)

        rows_loaded = 0
        for parquet_file in parquet_files:
            df = pd.read_parquet(parquet_file)
            for _, row in df.iterrows():
                row_dict = {k: (None if pd.isna(v) else v) for k, v in row.items()}
                cols = ", ".join(row_dict.keys())
                params = ", ".join(f":{k}" for k in row_dict.keys())
                try:
                    async with engine.begin() as conn:
                        await conn.execute(
                            text(f"INSERT INTO {schema}.{table_name} ({cols}) VALUES ({params}) ON CONFLICT DO NOTHING"),
                            row_dict,
                        )
                    rows_loaded += 1
                except IntegrityError:
                    print(f"  ⚠️  Skipped orphaned row in {schema}.{table_name}: {row_dict.get('id', '?')}")

        print(f"  ✅ Data loaded: {schema}.{table_name} ({strategy}, {rows_loaded} rows)")


async def _register_product(manifest: dict, relationships: list):
    product_id = manifest.get("id")
    if not product_id:
        print(f"  ⚠️  Skipping product '{manifest.get('name')}' — no id in product.json")
        return

    async with engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO system.products (id, name, type, description, status)
                VALUES (:id, :name, :type, :description, :status)
                ON CONFLICT (id) DO UPDATE
                    SET name        = EXCLUDED.name,
                        type        = EXCLUDED.type,
                        description = EXCLUDED.description,
                        status      = EXCLUDED.status,
                        modified_at = NOW()
            """),
            {
                "id": product_id,
                "name": manifest["name"],
                "type": manifest.get("type"),
                "description": manifest.get("description", ""),
                "status": manifest.get("status", "active"),
            },
        )

    # Collect inline children (products without their own product.json folder)
    # String children are UUID references to separate products — skip, the walker handles them
    for child in manifest.get("children", []):
        if isinstance(child, str):
            if product_id:
                relationships.append((product_id, child, "child"))
            continue
        await _register_inline_product(child, relationships)
        if product_id and child.get("id"):
            relationships.append((product_id, child["id"], "child"))

    # Collect declared foreign parents
    if product_id:
        for parent_id in manifest.get("parents", []):
            relationships.append((product_id, parent_id, "parent"))

    # Collect dependencies
    if product_id:
        for dep_id in manifest.get("dependencies", []):
            relationships.append((product_id, dep_id, "dependency"))


async def _register_inline_product(manifest: dict, relationships: list):
    product_id = manifest.get("id")
    if not product_id:
        print(f"  ⚠️  Skipping inline product '{manifest.get('name')}' — no id in product.json")
        return

    async with engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO system.products (id, name, type, description, status)
                VALUES (:id, :name, :type, :description, :status)
                ON CONFLICT (id) DO UPDATE
                    SET name        = EXCLUDED.name,
                        type        = EXCLUDED.type,
                        description = EXCLUDED.description,
                        status      = EXCLUDED.status,
                        modified_at = NOW()
            """),
            {
                "id": product_id,
                "name": manifest["name"],
                "type": manifest.get("type"),
                "description": manifest.get("description", ""),
                "status": manifest.get("status", "active"),
            },
        )

    # Recurse into nested children
    for child in manifest.get("children", []):
        if isinstance(child, str):
            if product_id:
                relationships.append((product_id, child, "child"))
            continue
        await _register_inline_product(child, relationships)
        if product_id and child.get("id"):
            relationships.append((product_id, child["id"], "child"))

    if product_id:
        for parent_id in manifest.get("parents", []):
            relationships.append((product_id, parent_id, "parent"))

    if product_id:
        for dep_id in manifest.get("dependencies", []):
            relationships.append((product_id, dep_id, "dependency"))


async def _register_relationship(source_id: str, target_id: str, kind: str):
    # A manifest can name a product that isn't on disk in this project home
    # (e.g. _root's parent). Skip that link instead of failing the bootstrap.
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("""
                    INSERT INTO system.product_relationships (source_id, target_id, kind)
                    VALUES (:source_id, :target_id, :kind)
                    ON CONFLICT DO NOTHING
                """),
                {"source_id": source_id, "target_id": target_id, "kind": kind},
            )
    except IntegrityError:
        print(f"  ⚠️  Skipping {kind} link {source_id} -> {target_id} — product not registered")
