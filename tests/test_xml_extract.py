"""Test weave_challenge module."""
from datetime import date
from pathlib import Path
from typing import Any, FrozenSet, Iterable, Tuple

import dateutil.parser
from py2neo import Node, Relationship, Subgraph

from weave_challenge.xml_extract import XML2GraphConfig, extract_graph


def create_xml_file(path: Path, content: str) -> Path:
    """Generate xml file.

    Args:
        path (Path): xml file path.
        content (str): xml document.

    Returns:
        File Path.
    """
    with path.open("w") as file:
        file.write(content)
    return path


def comparable_nodes(
    nodes: Iterable[Node],
) -> FrozenSet[Tuple[FrozenSet[Any], FrozenSet[Tuple[Any, Any]]]]:
    """Returns nodes in a comparable format.

    Args:
        nodes (Iterable[Node]): thee nodes iterable.

    Returns:
        Returns a frozenset and tuple representation of the collection of nodes.
    """
    return frozenset(
        (frozenset(node.labels), frozenset(node.items())) for node in nodes
    )


def equal_nodes(nodes: Iterable[Node], other_nodes: Iterable[Node]) -> bool:
    """Compares two node iterables.

    Args:
        nodes (Iterable[Node]): an nodes iterable to compare.
        other_nodes (Iterable[Node]): another nodes iterable to compare.

    Returns:
        True iff the two iterables contains exactly the same set of nodes.
    """
    return comparable_nodes(nodes) == comparable_nodes(other_nodes)


def has_relationships(
    relationships: Iterable[Relationship],
    relationship_tuples: Iterable[Tuple[str, str, str]],
) -> bool:
    """Determines if a relationships iterable corresponds to
    an iterable of tuples representing them.

    Args:
        relationships (Iterable[Relationship]): the relationships to evaluate.
        relationship_tuples (Iterable[Tuple[str, str, str]):
            tuples representing the relationships as
            (source_node_label, relationship_label, target_node_label).

    Returns:
        True iff the relationships correspond to the tuples representing them.
    """
    return frozenset(
        (
            frozenset(r.start_node.labels),
            type(r).__name__,
            frozenset(r.end_node.labels),
        )
        for r in relationships
    ) == frozenset(
        (frozenset([s]), r, frozenset([t])) for s, r, t in relationship_tuples
    )


def test_extract_graph_without_configuration(tmp_path: Path) -> None:
    """Test task for extracting a properties subgraph from a xml file,
        without configurations.

    Args:
        tmp_path: temporary directory for creating test data files.
    """
    xml_file_path: Path = create_xml_file(
        tmp_path / "example.xml",
        """<?xml version="1.0" encoding="UTF-8"  standalone="no" ?>
        <uniprot
        xmlns="http://uniprot.org/uniprot"
        xsi:schemaLocation="http://uniprot.org/uniprot"
        >
        <entry
            dataset="Swiss-Prot"
            created="2000-05-30"
        >
              <accession>Q9Y261</accession>
              <accession>Q8WUW4</accession>
              <protein>
                <recommendedName>
                  <fullName>Hepatocyte nuclear factor 3-beta</fullName>
                  <shortName>HNF-3B</shortName>
                </recommendedName>
              </protein>
        </entry>
    </uniprot>
    """,
    )

    subgraph: Subgraph = extract_graph(xml_file_path)

    assert len(subgraph.nodes) == 8
    assert len(subgraph.relationships) == 7

    assert equal_nodes(
        subgraph.nodes,
        [
            Node("Uniprot"),
            Node("Entry", dataset="Swiss-Prot", created="2000-05-30"),
            Node("Accession", value="Q9Y261"),
            Node("Accession", value="Q8WUW4"),
            Node("Protein"),
            Node("RecommendedName"),
            Node("FullName", value="Hepatocyte nuclear factor 3-beta"),
            Node("ShortName", value="HNF-3B"),
        ],
    )

    assert has_relationships(
        subgraph.relationships,
        [
            ("Uniprot", "HAS_ENTRY", "Entry"),
            ("Entry", "HAS_ACCESSION", "Accession"),
            ("Entry", "HAS_PROTEIN", "Protein"),
            ("Protein", "HAS_RECOMMENDED_NAME", "RecommendedName"),
            ("RecommendedName", "HAS_FULL_NAME", "FullName"),
            ("RecommendedName", "HAS_SHORT_NAME", "ShortName"),
        ],
    )


def test_extract_graph_with_node_lables_configuration(tmp_path: Path) -> None:
    """Test task for extracting a properties subgraph from a xml file,
       with custom node labels.

    Args:
        tmp_path: temporary directory for creating test data files.
    """
    xml_file_path: Path = create_xml_file(
        tmp_path / "example.xml",
        """<?xml version="1.0" encoding="UTF-8"  standalone="no" ?>
        <entry/>
        """,
    )

    config = XML2GraphConfig(
        node_labels={
            "entry": "Record",
        },
    )

    subgraph: Subgraph = extract_graph(xml_file_path, config)

    assert len(subgraph.nodes) == 1
    assert equal_nodes(
        subgraph.nodes,
        [
            Node("Record"),
        ],
    )


def test_extract_graph_with_custom_relationship_labels(tmp_path: Path) -> None:
    """Test task for extracting a properties subgraph from a xml file,
       with custom relationships labels.

    Args:
        tmp_path: temporary directory for creating test data files.
    """
    xml_file_path: Path = create_xml_file(
        tmp_path / "example.xml",
        """<uniprot>
            <entry></entry>
        </uniprot>
        """,
    )
    config = XML2GraphConfig(
        relationship_labels={
            "entry": "HAS_RECORD",
        },
    )

    subgraph: Subgraph = extract_graph(xml_file_path, config)
    assert len(subgraph.nodes) == 2
    assert len(subgraph.relationships) == 1
    assert has_relationships(
        subgraph.relationships,
        [
            ("Uniprot", "HAS_RECORD", "Entry"),
        ],
    )


def test_extract_graph_with_custom_property_names(tmp_path: Path) -> None:
    """Test task for extracting a properties subgraph from a xml file,
       with custom property names.

    Args:
        tmp_path: temporary directory for creating test data files.
    """
    xml_file_path: Path = create_xml_file(
        tmp_path / "example.xml",
        """<entry created="2000-05-30"></entry>""",
    )
    config = XML2GraphConfig(
        property_names={
            "entry": {
                "created": "created_at",
            }
        },
    )
    subgraph: Subgraph = extract_graph(xml_file_path, config)
    assert len(subgraph.nodes) == 1
    assert equal_nodes(
        subgraph.nodes,
        [
            Node("Entry", created_at="2000-05-30"),
        ],
    )


def test_extract_graph_with_custom_attribute_value_types(tmp_path: Path) -> None:
    """Test task for extracting a properties subgraph from a xml file,
       with custom attribute value type.

    Args:
        tmp_path: temporary directory for creating test data files.
    """
    xml_file_path: Path = create_xml_file(
        tmp_path / "example.xml",
        """
        <entry created="2000-05-30"></entry>
        """,
    )

    config = XML2GraphConfig(
        property_types={
            "entry": {"created": lambda v: dateutil.parser.parse(v).date()}
        },
    )

    subgraph: Subgraph = extract_graph(xml_file_path, config)

    assert len(subgraph.nodes) == 1

    assert equal_nodes(
        subgraph.nodes,
        [
            Node("Entry", created=date(2000, 5, 30)),
        ],
    )


def test_extract_graph_with_merges(tmp_path: Path) -> None:
    """Test task for extracting a properties subgraph from a xml file,
    configuring elements to merge with their parents.

    Args:
        tmp_path: temporary directory for creating test data files.
    """
    xml_file_path: Path = create_xml_file(
        tmp_path / "example.xml",
        """
        <entry dataset="Swiss-Prot" created="2000-05-30">
              <protein _id="Q9Y261"></protein>
        </entry>
    """,
    )

    config = XML2GraphConfig(elements_for_merging_with_parents={"protein"})
    subgraph: Subgraph = extract_graph(xml_file_path, config=config)

    assert len(subgraph.nodes) == 1
    assert len(subgraph.relationships) == 0

    assert equal_nodes(
        subgraph.nodes,
        [
            Node("Protein", _id="Q9Y261", dataset="Swiss-Prot", created="2000-05-30"),
        ],
    )
