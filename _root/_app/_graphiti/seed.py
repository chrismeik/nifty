from neo4j import AsyncDriver


async def seed_product(driver: AsyncDriver, manifest: dict) -> None:
    async with driver.session() as session:
        await session.run(
            """
            MERGE (p:Product {id: $id})
            SET p.name = $name,
                p.type = $type,
                p.description = $description,
                p.status = $status
            """,
            id=manifest["id"],
            name=manifest["name"],
            type=manifest.get("type") or "",
            description=manifest.get("description") or "",
            status=manifest.get("status") or "active",
        )


async def seed_relationship(driver: AsyncDriver, source_id: str, target_id: str, kind: str) -> None:
    if kind == "parent":
        return  # Redundant — HAS_CHILD from the other direction covers this
    rel_map = {"child": "HAS_CHILD", "dependency": "DEPENDS_ON"}
    rel_type = rel_map.get(kind)
    if not rel_type:
        return
    async with driver.session() as session:
        await session.run(
            f"MATCH (a:Product {{id: $source}}), (b:Product {{id: $target}}) "
            f"MERGE (a)-[:{rel_type}]->(b)",
            source=source_id,
            target=target_id,
        )
