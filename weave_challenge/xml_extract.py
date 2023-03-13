"""Provides XML parsing to extract properties graph."""
import dataclasses
import io
import xml.sax  # nosec the input XML are trusted
from pathlib import Path
from typing import Dict, List, Optional, Set

import py2neo


@dataclasses.dataclass
class XML2GraphConfig:
    """Configures how a XML document is translated into a properties graph,
    defining:
        - custom node labels for XML element types
        - custom property names for XML element attributes
        - custom relationships labels for XML childship relationships.
    """

    node_labels: Dict[str, str]
    property_names: Dict[str, Dict[str, str]]
    relationship_labels: Dict[str, str]


class PropertiesSubgraphHandler(xml.sax.ContentHandler):
    """SAX XML handler for collecting property graph's nodes and relationships."""

    META_ATTR_PREFIXES = {"xmlns", "xsi"}

    def __init__(
        self,
        nodes: Set[py2neo.Node],
        relationships: Set[py2neo.Relationship],
        config: Optional[XML2GraphConfig] = None,
    ) -> None:
        super().__init__()
        self.config: Optional[XML2GraphConfig] = config
        self.nodes: Set[py2neo.Node] = nodes
        self.relationships: Set[py2neo.Relationship] = relationships
        self.stack: List[py2neo.Node] = []
        self.text_stack: List[io.StringIO] = []

    @classmethod
    def _is_meta_attr(cls, attr: str) -> bool:
        return any(attr.startswith(prefix) for prefix in cls.META_ATTR_PREFIXES)

    def _node_label(self, element_name: str) -> str:
        if self.config and element_name in self.config.node_labels:
            return self.config.node_labels[element_name]

        return element_name[0].upper() + element_name[1:]

    def _relationship_label(self, element_name: str) -> str:
        if self.config and element_name in self.config.relationship_labels:
            return self.config.relationship_labels[element_name]
        return "HAS_" + element_name.upper()

    def _property_name(self, element_name: str, attr_name: str) -> str:
        if (
            self.config
            and element_name in self.config.property_names
            and attr_name in self.config.property_names[element_name]
        ):
            return self.config.property_names[element_name][attr_name]
        return attr_name

    def startElement(self, name: str, attrs: Dict[str, str]) -> None:
        node_label = self._node_label(name)
        properties: Dict[str, str] = {
            self._property_name(name, k): v
            for k, v in attrs.items()
            if not self._is_meta_attr(k)
        }
        node = py2neo.Node(node_label, **properties)
        self.nodes.add(node)
        if self.stack:
            relationship_label = self._relationship_label(name)
            parent_relationship = py2neo.Relationship(
                self.stack[-1], relationship_label, node
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


def extract_graph(
    xml_file: Path, config: Optional[XML2GraphConfig] = None
) -> py2neo.Subgraph:
    """Extracts a properties graphs from a XML file.

    Args:
        xml_file (Path): xml file to extract.
        config (XML2GraphConfig): configures XML to graph translation.

    Returns:
        A properties Subgraph extracted from the xml.
    """
    nodes: Set[py2neo.Node] = set()
    relationships: Set[py2neo.Relationship] = set()
    xml.sax.parse(  # nosect the input XML are trusted
        xml_file.absolute().as_posix(),
        PropertiesSubgraphHandler(nodes, relationships, config=config),
    )
    return py2neo.Subgraph(nodes, relationships)