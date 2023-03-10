"""Weave challenge data engineering coding challenge."""
from prefect import flow

__version__ = "0.1.0"


@flow()
def ingest_flow() -> None:
    """Data ingestion workflow."""
