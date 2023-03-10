"""Defines flow ingesting UnitProt xml files data into neo4j."""
from prefect import flow


@flow()
def ingest_unitprot_into_neo4j_flow() -> None:
    """Flow ingesting UnitProt xml files data into neo4j."""


if __name__ == "__main__":  # pragma: no cover
    ingest_unitprot_into_neo4j_flow()  # type: ignore
