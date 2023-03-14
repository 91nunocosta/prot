"""Defines flow ingesting UniProt xml files data into neo4j."""
import os
from pathlib import Path

import py2neo
from prefect import flow, task

from weave_challenge.uniprot2graph_config import UNITPROT2GRAPTH_CONFIG
from weave_challenge.xml_extract import extract_graph

DEFAULT_DATA_DIR = os.environ.get("DATA_DIR", "./data")


@task
def extract_from_xml(xml_file: Path) -> py2neo.Subgraph:
    """Task for extracting a properties subgraphs from a xml file.

    Args:
        xml_file (Path): xml file to extract.

    Returns:
        A properties Subgraph extracted from the xml.
    """
    return extract_graph(xml_file, UNITPROT2GRAPTH_CONFIG)


@task
def load_into_neo4j(subgraphs: py2neo.Subgraph) -> None:
    """Task for loading a properties Subgraph into neo4j.

    Args:
        subgraphs (py2neo.Subgraph): a properties Subgraphs.
    """
    graph = py2neo.Graph()
    for subgraph in subgraphs:
        graph.create(subgraph)


@flow()
def ingest_uniprot_into_neo4j_flow(data_directory_path: str = DEFAULT_DATA_DIR) -> None:
    """Flow ingesting UniProt xml files data into neo4j.

    Args:
        data_directory_path (str): path to the directory containing the
                                   XML UniProt files to ingest.
    """
    data_directory: Path = Path(data_directory_path)
    for xml_file in data_directory.glob("*.xml"):
        subgraphs: py2neo.Subgraph = extract_from_xml(xml_file)
        load_into_neo4j(subgraphs)


if __name__ == "__main__":  # pragma: no cover
    ingest_uniprot_into_neo4j_flow()  # type: ignore
