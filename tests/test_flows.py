"""Test weave_challenge module."""
from prefect.testing.utilities import prefect_test_harness

from weave_challenge.flows import ingest_unitprot_into_neo4j_flow


def test_ingest_unitprot_into_neo4j_flow() -> None:
    """Test running ingestion UnitProt data into neo4j flow,
    with a temporary testing database.
    """
    with prefect_test_harness():
        assert ingest_unitprot_into_neo4j_flow() is None  # type: ignore
