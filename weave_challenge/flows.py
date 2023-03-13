"""Defines flow ingesting UnitProt xml files data into neo4j."""
import xml.sax  # nosec the input XML are trusted
from pathlib import Path
from typing import Dict, Iterable, List

import py2neo
from prefect import flow, task


@task
def extract_from_xml(xml_file: Path) -> Iterable[py2neo.Subgraph]:
    """Task for extracting a stream of subgraphs from a xml file.

    Args:
        xml_file (Path): xml file to extract.

    Returns:
        An Iterable of Subgraph extracted from the xml.
    """
    nodes: List[py2neo.Node] = []
    relationships: List[py2neo.Relationship] = []

    class PropertiesSubgraphHandler(xml.sax.ContentHandler):
        """SAX XML handler for collecting property graph's nodes and relationships."""

        def __init__(
            self, nodes: List[py2neo.Node], relationships: List[py2neo.Relationship]
        ) -> None:
            super().__init__()
            self.nodes = nodes
            self.relationships = relationships
            self.stack: List[py2neo.Node] = []

        def startElement(self, name: str, attrs: Dict[str, str]) -> None:
            node = py2neo.Node(name, **dict(attrs))
            self.nodes.append(node)
            if self.stack:
                parent_relationship = py2neo.Relationship(
                    self.stack[-1], "HAS_" + name.upper(), node
                )
                self.relationships.append(parent_relationship)
            self.stack.append(node)

        def endElement(self, name: str) -> None:
            self.stack.pop()

    xml.sax.parse(  # nosect the input XML are trusted
        xml_file.absolute().as_posix(), PropertiesSubgraphHandler(nodes, relationships)
    )
    return [py2neo.Subgraph(nodes, relationships)]


@task
def load_into_neo4j(subgraphs: Iterable[py2neo.Subgraph]) -> None:
    """Task for loading a stream of subgraphs into neo4j.

    Args:
        subgraphs (Iterable[py2neo.Subgraph): stream of subgraphs.
    """
    graph = py2neo.Graph()
    for subgraph in subgraphs:
        graph.create(subgraph)


@flow()
def ingest_unitprot_into_neo4j_flow() -> None:
    """Flow ingesting UnitProt xml files data into neo4j."""
    xml_file = Path(__file__).parent.parent / "data" / "Q9Y261.xml"
    subgraphs: Iterable[py2neo.Subgraph] = extract_from_xml(xml_file)  # type: ignore
    load_into_neo4j(subgraphs)


if __name__ == "__main__":  # pragma: no cover
    ingest_unitprot_into_neo4j_flow()  # type: ignore
