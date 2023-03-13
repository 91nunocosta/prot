"""Test weave_challenge module."""
from pathlib import Path
from typing import FrozenSet, Iterable, Tuple

from py2neo import Node, Subgraph

from weave_challenge.xml_extract import extract_graph


def test_task_extract_from_xml(tmp_path: Path) -> None:
    """Test task for extracting a properties subgraph from a xml file.

    Args:
        tmp_path: temporary directory for creating test data files.
    """
    xml_document: str = """<?xml version="1.0" encoding="UTF-8"  standalone="no" ?>
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
    """
    xml_file_path: Path = tmp_path / "example.xml"
    with xml_file_path.open("w") as xml_file:
        xml_file.write(xml_document)

    subgraph: Subgraph = extract_graph(
        xml_file_path,
    )

    assert len(subgraph.nodes) == 8
    assert len(subgraph.relationships) == 7

    nodes = {
        Node("uniprot"),
        Node("entry", dataset="Swiss-Prot", created="2000-05-30"),
        Node("accession", value="Q9Y261"),
        Node("accession", value="Q8WUW4"),
        Node("protein"),
        Node("recommendedName"),
        Node("fullName", value="Hepatocyte nuclear factor 3-beta"),
        Node("shortName", value="HNF-3B"),
    }

    def comparable(
        nodes: Iterable[Node],
    ) -> FrozenSet[Tuple[FrozenSet[str], FrozenSet[Tuple[str, str]]]]:
        return frozenset(
            (frozenset(node.labels), frozenset(node.items())) for node in nodes
        )

    assert comparable(subgraph.nodes) == comparable(nodes)

    assert frozenset(
        (frozenset(r.start_node.labels), type(r).__name__, frozenset(r.end_node.labels))
        for r in subgraph.relationships
    ) == frozenset(
        (frozenset([s]), r, frozenset([t]))
        for s, r, t in [
            ("uniprot", "HAS_ENTRY", "entry"),
            ("entry", "HAS_ACCESSION", "accession"),
            ("entry", "HAS_PROTEIN", "protein"),
            ("protein", "HAS_RECOMMENDEDNAME", "recommendedName"),
            ("recommendedName", "HAS_FULLNAME", "fullName"),
            ("recommendedName", "HAS_SHORTNAME", "shortName"),
        ]
    )
