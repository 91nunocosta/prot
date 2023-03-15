"""Configures UniProt translation into properties graph."""
from prot.xml_extract import XML2GraphConfig

UNITPROT2GRAPTH_CONFIG = XML2GraphConfig(
    node_labels={
        "person": "Author",
    },
    relationship_labels={
        "organism": "IN_ORGANISM",
        "gene": "FROM_GENE",
    },
    collection_elements={
        "authorList": "HAS_AUTHOR",
    },
    elements_for_merging_with_parents={"protein"},
)
