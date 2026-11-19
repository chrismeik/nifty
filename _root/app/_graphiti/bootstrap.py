import json
from pathlib import Path
from _app._graphiti.client import get_driver, get_graphiti
from _app._graphiti.seed import seed_product, seed_relationship

ROOT_DIR = Path("/root-product")


async def init():
    await get_graphiti().build_indices_and_constraints()

    relationships: list[tuple[str, str, str]] = []
    await _walk(ROOT_DIR, relationships)

    for source_id, target_id, kind in relationships:
        await seed_relationship(get_driver(), source_id, target_id, kind)

    print("✅ Graph bootstrap complete")


async def _walk(product_dir: Path, relationships: list):
    manifest_path = product_dir / "product.json"
    if not manifest_path.exists():
        return

    manifest = json.loads(manifest_path.read_text())
    product_id = manifest.get("id")
    if not product_id:
        return

    await seed_product(get_driver(), manifest)

    for child_id in manifest.get("children", []):
        if isinstance(child_id, str):
            relationships.append((product_id, child_id, "child"))

    for dep_id in manifest.get("depends_on", []):
        if isinstance(dep_id, str):
            relationships.append((product_id, dep_id, "dependency"))

    for sub_dir in sorted(product_dir.iterdir()):
        if sub_dir.is_dir() and not sub_dir.name.startswith("."):
            if (sub_dir / "product.json").exists():
                await _walk(sub_dir, relationships)
