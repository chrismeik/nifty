import os
from neo4j import AsyncGraphDatabase, AsyncDriver
from graphiti_core import Graphiti

_driver: AsyncDriver | None = None
_graphiti: Graphiti | None = None


def get_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
        )
    return _driver


def get_graphiti() -> Graphiti:
    global _graphiti
    if _graphiti is None:
        _graphiti = Graphiti(
            os.environ["NEO4J_URI"],
            os.environ["NEO4J_USER"],
            os.environ["NEO4J_PASSWORD"],
        )
    return _graphiti
