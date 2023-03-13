"""Test weave_challenge flows."""
from prefect.testing.utilities import prefect_test_harness
from py2neo import Graph, Node, Relationship

from weave_challenge.flows import ingest_unitprot_into_neo4j_flow, load_into_neo4j


def test_task_load_into_neo4j() -> None:
    """Test loading a stream of subgraphs into neo4j."""
    graph = Graph()
    graph.delete_all()

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

    graph.delete_all()


def test_ingest_unitprot_into_neo4j_flow() -> None:
    """Test running ingestion UnitProt data into neo4j flow,
    with a temporary testing database.
    """
    with prefect_test_harness():
        assert ingest_unitprot_into_neo4j_flow()  # type: ignore
