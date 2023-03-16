"""Provides XML parsing to extract properties graph."""
import io
import xml.sax  # nosec the input XML are trusted
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import inflection
import py2neo


class XML2GraphConfig:  # pylint: disable=too-few-public-methods
    """Configures how to translate an XML document into a properties graph."""

    def __init__(  # pylint: disable=too-many-arguments,
        self,
        node_labels: Optional[Dict[str, str]] = None,
        property_names: Optional[Dict[Tuple[str, str], str]] = None,
        property_types: Optional[Dict[Tuple[str, str], Callable[[str], Any]]] = None,
        relationship_labels: Optional[Dict[str, str]] = None,
        elements_for_merging_with_parents: Optional[Set[str]] = None,
        collection_elements: Optional[Dict[str, str]] = None,
    ) -> None:
        """Configures how to translate an XML document into a properties graph.

        Args:
            node_labels:
                Maps XML element names into target nodes labels.
                Example:
                    {"entry": "Record"}
            property_names:
                Maps pairs of XML element and attribute names into target node property
                names.
                Example:
                    {("entry","created"): "created_at")}
            property_types:
                Maps pairs of XML element and property names into callables for
                coercing their values.
                Example:
                    {("entry", "created"): lambda v: dateutil.parser.parse(v)}
            relationship_labels:
                Maps XML element names into the label for the relationship of
                the parent node with it.
                Example:
                    {"entry": "HAS_RECORD"}
            elements_for_merging_with_parents:
                Defines a set of XML elements to merge with parent nodes.
                The listed XML elements aren't translated into new nodes.
                Instead, the extractor merges them into the nodes corresponding to
                their XML parents.
                Their labels replace the parent labels.
                Their attributes extend the parent node properties.
                Example:
                    {"protein"}
            collection_elements:
                Specifies which XML elements aggregate relationships between
                their parent and their children.
                The listed XML elements aren't translated into new nodes.
                Instead, the extractor creates a relationship between their parent
                and each child.
                This parameter maps the XML element name into the label of
                the relationships to create.
                Example:
                    {"authorList": "HAS_AUTHOR"}
        """
        if node_labels is None:
            self.node_labels: Dict[str, str] = {}
        else:
            self.node_labels = node_labels
        if property_names is None:
            self.property_names: Dict[Tuple[str, str], str] = {}
        else:
            self.property_names = property_names
        if property_types is None:
            self.property_types: Dict[Tuple[str, str], Callable[[str], Any]] = {}
        else:
            self.property_types = property_types
        if relationship_labels is None:
            self.relationship_labels: Dict[str, str] = {}
        else:
            self.relationship_labels = relationship_labels
        if elements_for_merging_with_parents is None:
            self.elements_for_merging_with_parents: Set[str] = set()
        else:
            self.elements_for_merging_with_parents = elements_for_merging_with_parents
        if collection_elements is None:
            self.collection_elements: Dict[str, str] = {}
        else:
            self.collection_elements = collection_elements


class PropertiesSubgraphHandler(xml.sax.ContentHandler):
    """SAX XML handler for collecting property graph's nodes and relationships."""

    META_ATTR_PREFIXES = {"xmlns", "xsi"}
    ELEMENT_TEXT_PROPERTY_NAME = "value"

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
        self.nodes_stack: List[py2neo.Node] = []
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
        if self.active_collection_element:
            return self.config.collection_elements[self.active_collection_element]

        if element_name in self.config.relationship_labels:
            return self.config.relationship_labels[element_name]
        return "HAS_" + inflection.underscore(element_name).upper()

    def _property_name(self, element_name: str, attr_name: str) -> str:
        if (element_name, attr_name) in self.config.property_names:
            return self.config.property_names[element_name, attr_name]
        return attr_name

    def _property_value(
        self, element_name: str, attr_name: str, attr_value: str
    ) -> Any:
        if (element_name, attr_name) in self.config.property_types:
            return self.config.property_types[element_name, attr_name](attr_value)
        return attr_value

    def _start_collection(self, name: str) -> None:
        self.active_collection_element = name

    def _merge_with_parent(self, node_label: str, properties: Dict[str, Any]) -> None:
        node = self.nodes_stack[-1]
        node.clear_labels()
        node.add_label(node_label)
        node.update(properties)

    def _create_new_node(
        self, node_label: str, properties: Dict[str, Any], relationship_label: str
    ) -> None:
        node = py2neo.Node(node_label, **properties)
        self.nodes.add(node)
        if self.nodes_stack:
            parent_relationship = py2neo.Relationship(
                self.nodes_stack[-1], relationship_label, node
            )
            self.relationships.add(parent_relationship)
        self.nodes_stack.append(node)
        self.text_stack.append(io.StringIO())

    def startElement(self, name: str, attrs: Dict[str, str]) -> None:
        node_label = self._node_label(name)
        properties: Dict[str, str] = {
            self._property_name(name, k): self._property_value(name, k, v)
            for k, v in attrs.items()
            if not self._is_meta_attr(k)
        }
        relationship_label = self._relationship_label(name)
        if name in self.config.collection_elements:
            self._start_collection(name)
        elif name in self.config.elements_for_merging_with_parents and self.nodes_stack:
            self._merge_with_parent(node_label, properties)
        else:
            self._create_new_node(node_label, properties, relationship_label)

    def characters(self, content: str) -> None:
        if self.text_stack:
            self.text_stack[-1].write(content)

    def endElement(self, name: str) -> None:
        if (
            self.nodes_stack
            and name not in self.config.elements_for_merging_with_parents
        ):
            node = self.nodes_stack.pop()
            element_text: str = self.text_stack.pop().getvalue().strip()
            if element_text:
                node[self.ELEMENT_TEXT_PROPERTY_NAME] = element_text
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
