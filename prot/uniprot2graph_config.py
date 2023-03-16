"""Configures UniProt translation into properties graph."""
import dateutil.parser

from prot.xml_extract import XML2GraphConfig

UNITPROT2GRAPTH_CONFIG = XML2GraphConfig(
    node_labels={
        "person": "Author",
    },
    property_types={
        ("entry", "created"): (
            lambda v: dateutil.parser.parse(v)  # pylint: disable=unnecessary-lambda
        )
    },
    relationship_labels={
        "organism": "IN_ORGANISM",
        "gene": "FROM_GENE",
    },
    collection_elements={
        "authorList": "HAS_AUTHOR",
    },
    elements_for_merging_with_parents={"entry", "protein"},
)
