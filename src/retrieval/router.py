from __future__ import annotations

import re

from retrieval.schema import RouteDecision

ALL_COLLECTIONS = [
    "gene_info",
    "ldsc_genetic_correlation",
    "gene_association_common",
    "gene_association_rare",
]

_LDSC_RE = re.compile(
    r"\b(ldsc|genetic correlation|genetically correlated|trait[- ]versus[- ]trait|2hri|"
    r"2-hour insulin|ogtt insulin)\b",
    re.IGNORECASE,
)
_COMMON_RE = re.compile(
    r"\b(common[- ]variant|common variants|gwas|bf_common)\b",
    re.IGNORECASE,
)
_RARE_RE = re.compile(
    r"\b(rare[- ]variant|rare variants|bf_rare|gene-based test|gene based test)\b",
    re.IGNORECASE,
)
_ASSOC_RE = re.compile(
    r"\b(association|associated with|gene-phenotype|gene phenotype|huge)\b",
    re.IGNORECASE,
)
_BOTH_ASSOC_RE = re.compile(
    r"\b(common and rare|rare and common|common-and-rare)\b",
    re.IGNORECASE,
)
_GENE_RE = re.compile(
    r"\b(gene function|function of|alternative names?|alias|ensembl|hgnc|entrez|uniprot|"
    r"genomic location|coordinates|which gene|identified by|ensg[0-9]+)\b",
    re.IGNORECASE,
)


def route_query(query: str) -> RouteDecision:
    matched: list[str] = []
    collections: set[str] = set()

    common = bool(_COMMON_RE.search(query))
    rare = bool(_RARE_RE.search(query))
    both = bool(_BOTH_ASSOC_RE.search(query))
    assoc = bool(_ASSOC_RE.search(query))
    ldsc = bool(_LDSC_RE.search(query))
    gene = bool(_GENE_RE.search(query))

    if both or (common and rare):
        collections.update(["gene_association_common", "gene_association_rare"])
        matched.append("explicit_common_and_rare")
    else:
        if common:
            collections.add("gene_association_common")
            matched.append("explicit_common_variant")
        if rare:
            collections.add("gene_association_rare")
            matched.append("explicit_rare_variant")
        if assoc and not common and not rare and not ldsc:
            collections.update(["gene_association_common", "gene_association_rare"])
            matched.append("association_without_variant_class")

    if ldsc:
        collections.add("ldsc_genetic_correlation")
        matched.append("ldsc_or_trait_correlation")

    if gene:
        collections.add("gene_info")
        matched.append("gene_function_or_identifier")

    if not collections:
        return RouteDecision(collections=list(ALL_COLLECTIONS), matched_rules=["unmatched_all_collections"])

    ordered = [name for name in ALL_COLLECTIONS if name in collections]
    return RouteDecision(collections=ordered, matched_rules=matched)
