"""Defines flow ingesting UnitProt xml files data into neo4j."""
from typing import Iterable

import py2neo
from prefect import flow, task


@task
def load_into_neo4j(subgraphs: Iterable[py2neo.Subgraph]) -> None:
    """Task loading a stream of subgraphs into neo4j.

    Args:
        subgraphs (Iterable[py2neo.Subgraph): stream of subgraphs.
    """
    graph = py2neo.Graph()
    for subgraph in subgraphs:
        graph.create(subgraph)


@flow()
def ingest_unitprot_into_neo4j_flow() -> None:
    """Flow ingesting UnitProt xml files data into neo4j."""


if __name__ == "__main__":  # pragma: no cover
    ingest_unitprot_into_neo4j_flow()  # type: ignore
