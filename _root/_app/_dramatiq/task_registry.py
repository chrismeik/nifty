"""
Auto-discovers and imports <product>._app.worker for all products that define one.
Imported by the Dramatiq worker so all product actors are registered before the
worker starts consuming messages.
"""

import importlib
import json
import logging
import sys
from pathlib import Path

log = logging.getLogger(__name__)

ROOT_DIR = Path("/root-product")


def _walk_product_tasks(product_dir: Path) -> None:
    manifest_path = product_dir / "product.json"
    if not manifest_path.exists():
        # The project home (e.g. veratree/bot) has no manifest of its own,
        # so start from the products in its subfolders.
        if product_dir == ROOT_DIR:
            for sub_dir in sorted(product_dir.iterdir()):
                if sub_dir.is_dir() and not sub_dir.name.startswith(("_", ".")):
                    _walk_product_tasks(sub_dir)
        return

    name = json.loads(manifest_path.read_text())["name"]
    app_slot = "_app" if (product_dir / "_app").is_dir() else "app"
    worker_path = product_dir / app_slot / "worker.py"

    if worker_path.exists():
        # Add all ancestor dirs up to ROOT_DIR so nested imports resolve correctly
        ancestor = product_dir.parent
        while True:
            p = str(ancestor)
            if p not in sys.path:
                sys.path.insert(0, p)
            if ancestor == ROOT_DIR or ancestor.parent == ancestor:
                break
            ancestor = ancestor.parent
        try:
            importlib.import_module(f"{name}.{app_slot}.worker")
            log.info("registered worker: %s", name)
        except Exception:
            log.exception("failed to register worker: %s", name)

    for sub_dir in sorted(product_dir.iterdir()):
        if sub_dir.is_dir() and not sub_dir.name.startswith(("_", ".")):
            _walk_product_tasks(sub_dir)


_walk_product_tasks(ROOT_DIR)
