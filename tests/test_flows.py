"""Test prot flows."""
from pathlib import Path
from typing import Iterable

import pytest
from prefect.testing.utilities import prefect_test_harness
from py2neo import Graph, Node, Relationship, Subgraph

from prot.flows import extract_from_xml, ingest_uniprot_into_neo4j_flow, load_into_neo4j


@pytest.fixture
def graph() -> Iterable[Graph]:
    """Returns a clean graph instance.

    Yields:
        Graph instance.
    """
    _graph = Graph()
    _graph.delete_all()
    yield _graph
    _graph.delete_all()


def test_task_extract_from_xml() -> None:
    """Test extracting the graph from the file using the uniprot2graph_config."""
    xml_file: Path = Path(__file__).parent.parent / "data" / "Q9Y261.xml"
    subgraph: Subgraph = extract_from_xml.fn(xml_file)
    assert len(subgraph.nodes) > 0
    assert len(subgraph.relationships) > 0


def test_task_load_into_neo4j(
    graph: Graph,  # pylint: disable=redefined-outer-name
) -> None:
    """Test loading a property graph into neo4j.

    Args:
        graph (Graph): clean py2neo Graph instance
    """
    alice = Node("Person", name="Alice")
    bob = Node("Person", name="Bob")
    carol = Node("Person", name="Carol")
    knows = Relationship.type("KNOWS")
    alice_bob = knows(alice, bob)
    bob_alice = knows(bob, alice)
    alice_carol = knows(alice, carol)
    carol_alice = knows(carol, alice)
    bob_carol = knows(bob, carol)
    carol_bob = knows(carol, bob)
    friends = alice_bob | bob_alice | alice_carol | carol_alice | bob_carol | carol_bob
    load_into_neo4j.fn(friends)
    assert len(graph.nodes) == 3


def test_ingest_uniprot_into_neo4j_flow(
    graph: Graph,  # pylint: disable=redefined-outer-name
) -> None:
    """Test running ingestion UniProt data into neo4j flow,
    with a temporary testing database.

    Args:
        graph (Graph): clean Graph instance

    """
    with prefect_test_harness():
        assert ingest_uniprot_into_neo4j_flow()  # type: ignore

    assert len(graph.nodes) > 0
    assert len(graph.relationships) > 0
