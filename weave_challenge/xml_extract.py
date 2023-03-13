"""Provides XML parsing to extract properties graph."""
import io
import xml.sax  # nosec the input XML are trusted
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import inflection
import py2neo


@dataclass
class XML2GraphConfig:
    """Configures how a XML document is translated into a properties graph,
    defining:
        - custom node labels for XML element types;
        - custom property names for XML element attributes;
        - custom relationships labels for XML childship relationships;
        - elements to merge with their parents, replacing their parent name and
        moving their attributes to their parents
        - elements which aren't nodes and represent collections.
    """

    node_labels: Dict[str, str] = field(default_factory=dict)
    property_names: Dict[str, Dict[str, str]] = field(default_factory=dict)
    property_types: Dict[str, Dict[str, Callable[[str], Any]]] = field(
        default_factory=dict
    )
    relationship_labels: Dict[str, str] = field(default_factory=dict)
    elements_for_merging_with_parents: Set[str] = field(default_factory=set)
    collection_elements: Dict[str, str] = field(default_factory=dict)


class PropertiesSubgraphHandler(xml.sax.ContentHandler):
    """SAX XML handler for collecting property graph's nodes and relationships."""

    META_ATTR_PREFIXES = {"xmlns", "xsi"}

    def __init__(
        self,
        nodes: Set[py2neo.Node],
        relationships: Set[py2neo.Relationship],
        config: XML2GraphConfig = XML2GraphConfig(),
    ) -> None:
        super().__init__()
        self.config: XML2GraphConfig = config
        self.nodes: Set[py2neo.Node] = nodes
        self.relationships: Set[py2neo.Relationship] = relationships
        self.stack: List[py2neo.Node] = []
        self.text_stack: List[io.StringIO] = []
        self.active_collection_element: Optional[str] = None

    @classmethod
    def _is_meta_attr(cls, attr: str) -> bool:
        return any(attr.startswith(prefix) for prefix in cls.META_ATTR_PREFIXES)

    def _node_label(self, element_name: str) -> str:
        if element_name in self.config.node_labels:
            return self.config.node_labels[element_name]

        return element_name[0].upper() + element_name[1:]

    def _relationship_label(self, element_name: str) -> str:
        if self.active_collection_element and self.config:
            return self.config.collection_elements[self.active_collection_element]

        if element_name in self.config.relationship_labels:
            return self.config.relationship_labels[element_name]
        return "HAS_" + inflection.underscore(element_name).upper()

    def _property_name(self, element_name: str, attr_name: str) -> str:
        if (
            element_name in self.config.property_names
            and attr_name in self.config.property_names[element_name]
        ):
            return self.config.property_names[element_name][attr_name]
        return attr_name

    def _property_value(
        self, element_name: str, attr_name: str, attr_value: str
    ) -> Any:
        if (
            element_name in self.config.property_types
            and attr_name in self.config.property_types[element_name]
        ):
            return self.config.property_types[element_name][attr_name](attr_value)
        return attr_value

    def startElement(self, name: str, attrs: Dict[str, str]) -> None:
        node_label = self._node_label(name)
        properties: Dict[str, str] = {
            self._property_name(name, k): self._property_value(name, k, v)
            for k, v in attrs.items()
            if not self._is_meta_attr(k)
        }
        relationship_label = self._relationship_label(name)

        if self.config.collection_elements and name in self.config.collection_elements:
            self.active_collection_element = name
            return

        if (
            self.config.elements_for_merging_with_parents
            and name in self.config.elements_for_merging_with_parents
            and self.stack
        ):
            node = self.stack[-1]
            node.clear_labels()
            node.add_label(node_label)
            node.update(properties)
            return

        node = py2neo.Node(node_label, **properties)
        self.nodes.add(node)
        if self.stack:
            parent_relationship = py2neo.Relationship(
                self.stack[-1], relationship_label, node
            )
            self.relationships.add(parent_relationship)
        self.stack.append(node)
        self.text_stack.append(io.StringIO())

    def characters(self, content: str) -> None:
        if self.text_stack:
            self.text_stack[-1].write(content)

    def endElement(self, name: str) -> None:
        if self.stack:
            if name not in self.config.elements_for_merging_with_parents:
                parent = self.stack.pop()
                if self.text_stack:
                    txt: str = self.text_stack[-1].getvalue().strip()
                    if txt:
                        parent["value"] = txt
                self.text_stack.pop()
        if self.active_collection_element == name:
            self.active_collection_element = None


def extract_graph(
    xml_file: Path, config: XML2GraphConfig = XML2GraphConfig()
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
