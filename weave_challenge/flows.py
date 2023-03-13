"""Defines flow ingesting UnitProt xml files data into neo4j."""
from pathlib import Path

import py2neo
from prefect import flow, task

from weave_challenge.uniprot2graph_config import UNITPROT2GRAPTH_CONFIG
from weave_challenge.xml_extract import extract_graph


@task
def extract_from_xml(xml_file: Path) -> py2neo.Subgraph:
    """Task for extracting a properties subgraphs from a xml file.

    Args:
        xml_file (Path): xml file to extract.

    Returns:
        A properties Subgraph extracted from the xml.
    """
    return extract_graph(xml_file, UNITPROT2GRAPTH_CONFIG)


@task
def load_into_neo4j(subgraphs: py2neo.Subgraph) -> None:
    """Task for loading a properties Subgraph into neo4j.

    Args:
        subgraphs (py2neo.Subgraph): a properties Subgraphs.
    """
    graph = py2neo.Graph()
    for subgraph in subgraphs:
        graph.create(subgraph)


@flow()
def ingest_unitprot_into_neo4j_flow() -> None:
    """Flow ingesting UnitProt xml files data into neo4j."""
    xml_file = Path(__file__).parent.parent / "data" / "Q9Y261.xml"
    subgraphs: py2neo.Subgraph = extract_from_xml(xml_file)
    load_into_neo4j(subgraphs)


if __name__ == "__main__":  # pragma: no cover
    ingest_unitprot_into_neo4j_flow()  # type: ignore
