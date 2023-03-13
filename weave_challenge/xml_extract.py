"""Provides XML parsing to extract properties graph."""
import io
import xml.sax  # nosec the input XML are trusted
from pathlib import Path
from typing import Dict, List, Set

import py2neo


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
        self.text_stack: List[io.StringIO] = []

    @classmethod
    def _is_meta_attr(cls, attr: str) -> bool:
        return any(attr.startswith(prefix) for prefix in cls.META_ATTR_PREFIXES)

    def _node_label(self, element_name: str) -> str:
        if not element_name:
            return ""

        return element_name[0].upper() + element_name[1:]

    def startElement(self, name: str, attrs: Dict[str, str]) -> None:
        node_label = self._node_label(name)
        properties: Dict[str, str] = {
            k: v for k, v in attrs.items() if not self._is_meta_attr(k)
        }
        node = py2neo.Node(node_label, **properties)
        self.nodes.add(node)
        if self.stack:
            parent_relationship = py2neo.Relationship(
                self.stack[-1], "HAS_" + name.upper(), node
            )
            self.relationships.add(parent_relationship)
        self.stack.append(node)
        self.text_stack.append(io.StringIO())

    def characters(self, content: str) -> None:
        self.text_stack[-1].write(content)

    def endElement(self, _: str) -> None:
        parent = self.stack.pop()
        if self.text_stack:
            txt: str = self.text_stack[-1].getvalue().strip()
            if txt:
                parent["value"] = txt
        self.text_stack.pop()


def extract_graph(xml_file: Path) -> py2neo.Subgraph:
    """Extracts a properties graphs from a XML file.

    Args:
        xml_file (Path): xml file to extract.

    Returns:
        A properties Subgraph extracted from the xml.
    """
    nodes: Set[py2neo.Node] = set()
    relationships: Set[py2neo.Relationship] = set()
    xml.sax.parse(  # nosect the input XML are trusted
        xml_file.absolute().as_posix(), PropertiesSubgraphHandler(nodes, relationships)
    )
    return py2neo.Subgraph(nodes, relationships)
