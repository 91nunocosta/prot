"""Defines flow ingesting UnitProt xml files data into neo4j."""
import xml.sax  # nosec the input XML are trusted
from pathlib import Path
from typing import Dict, List, Set

import py2neo
from prefect import flow, task


@task
def extract_from_xml(xml_file: Path) -> py2neo.Subgraph:
    """Task for extracting a properties subgraphs from a xml file.

    Args:
        xml_file (Path): xml file to extract.

    Returns:
        A properties Subgraph extracted from the xml.
    """
    nodes: Set[py2neo.Node] = set()
    relationships: Set[py2neo.Relationship] = set()

    class PropertiesSubgraphHandler(xml.sax.ContentHandler):
        """SAX XML handler for collecting property graph's nodes and relationships."""

        META_ATTR_PREFIXES = {"xmlns", "xsi"}

        def __init__(
            self,
            nodes: Set[py2neo.Node],
            relationships: Set[py2neo.Relationship],
        ) -> None:
            super().__init__()
            self.nodes: Set[py2neo.Node] = nodes
            self.relationships: Set[py2neo.Relationship] = relationships
            self.stack: List[py2neo.Node] = []

        @classmethod
        def _is_meta_attr(cls, attr: str) -> bool:
            return any(attr.startswith(prefix) for prefix in cls.META_ATTR_PREFIXES)

        def startElement(self, name: str, attrs: Dict[str, str]) -> None:
            properties: Dict[str, str] = {
                k: v for k, v in attrs.items() if not self._is_meta_attr(k)
            }
            node = py2neo.Node(name, **properties)
            self.nodes.add(node)
            if self.stack:
                parent_relationship = py2neo.Relationship(
                    self.stack[-1], "HAS_" + name.upper(), node
                )
                self.relationships.add(parent_relationship)
            self.stack.append(node)

        def endElement(self, _: str) -> None:
            self.stack.pop()

    xml.sax.parse(  # nosect the input XML are trusted
        xml_file.absolute().as_posix(), PropertiesSubgraphHandler(nodes, relationships)
    )
    return py2neo.Subgraph(nodes, relationships)


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
