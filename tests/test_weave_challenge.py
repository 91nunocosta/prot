"""Test weave_challenge module."""
from prefect.testing.utilities import prefect_test_harness

from weave_challenge import ingest_flow


def test_ingest_flow() -> None:
    """Test running ingestion workflow, with a temporary testing database."""
    with prefect_test_harness():
        assert ingest_flow() is None  # type: ignore
