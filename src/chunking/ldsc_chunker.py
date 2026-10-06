from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterator

from chunking.phenotype_glossary import PhenotypeGlossary, ancestry_label
from chunking.schema import Chunk
from chunking.utils import load_jsonl, relative_source_path, significance_tag


ANCESTRY_ORDER = ["Mixed", "EU", "HS"]


def chunk_ldsc_pairs(
    jsonl_path: Path,
    glossary: PhenotypeGlossary,
    project_root: Path,
) -> Iterator[Chunk]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    raw_row_count = 0

    for row in load_jsonl(jsonl_path):
        raw_row_count += 1
        key = (row["phenotype"], row["other_phenotype"])
        grouped[key].append(row)

    source_file_rel = relative_source_path(jsonl_path, project_root)

    for (phenotype, other_phenotype), results in sorted(grouped.items()):
        phenotype_label, phenotype_label_confidence = glossary.get_label(phenotype)
        other_label, other_label_confidence = glossary.get_label(other_phenotype)
        other_category = glossary.get_category(other_phenotype)

        sorted_results = sorted(
            results,
            key=lambda item: (
                ANCESTRY_ORDER.index(item["ancestry"])
                if item["ancestry"] in ANCESTRY_ORDER
                else len(ANCESTRY_ORDER)
            ),
        )

        mixed_result = next((item for item in sorted_results if item["ancestry"] == "Mixed"), None)
        mixed_rg = mixed_result["rg"] if mixed_result else None
        mixed_pvalue = mixed_result["pValue"] if mixed_result else None
        is_significant_mixed = bool(mixed_result and mixed_result["pValue"] < 0.05)
        project = sorted_results[0].get("project", "portal")

        result_lines = []
        for item in sorted_results:
            result_lines.append(
                f"- {ancestry_label(item['ancestry'])}: "
                f"rg={item['rg']:.4g}, SE={item['stdErr']:.4g}, p={item['pValue']:.4g}"
                f"{significance_tag(item['pValue'])}"
            )

        summary_line = "Summary (Mixed ancestry): not available"
        if mixed_result:
            summary_line = (
                f"Summary (Mixed ancestry): rg={mixed_rg:.4g}, p={mixed_pvalue:.4g}, "
                f"significant={str(is_significant_mixed).lower()}"
            )

        content_lines = [
            (
                "Genetic correlation analysis (LDSC): "
                f"{phenotype_label} ({phenotype}) vs {other_label} ({other_phenotype})"
            ),
            "Analysis type: Linkage Disequilibrium Score Regression (LDSC)",
            (
                "Anchor trait: 2-hour insulin from oral glucose tolerance test (OGTT), "
                "a quantitative metabolic trait studied at population level via GWAS summary statistics."
            ),
            "",
            "Results by ancestry:",
            *result_lines,
            "",
            summary_line,
            "",
            "Interpretation boundaries:",
            "- rg reflects shared genetic architecture between traits, not causal effect.",
            "- Results describe population-level GWAS evidence, not individual lab test values.",
            "- Non-significant p-values indicate insufficient evidence for shared genetic basis under this analysis.",
            "",
            f"Source: T2D Knowledge Portal LDSC results (project={project})",
            f"Provenance: {source_file_rel}",
        ]

        metadata_results = [
            {
                "ancestry": item["ancestry"],
                "rg": item["rg"],
                "stdErr": item["stdErr"],
                "pValue": item["pValue"],
            }
            for item in sorted_results
        ]

        metadata = {
            "entity_type": "genetic_correlation",
            "phenotype": phenotype,
            "phenotype_label": phenotype_label,
            "phenotype_label_confidence": phenotype_label_confidence,
            "other_phenotype": other_phenotype,
            "other_phenotype_label": other_label,
            "other_phenotype_label_confidence": other_label_confidence,
            "other_phenotype_category": other_category,
            "results": metadata_results,
            "mixed_rg": mixed_rg,
            "mixed_pvalue": mixed_pvalue,
            "is_significant_mixed": is_significant_mixed,
            "available_ancestries": [item["ancestry"] for item in sorted_results],
            "project": project,
            "method": "LDSC",
            "source_file": source_file_rel,
            "raw_row_count_for_pair": len(sorted_results),
        }

        citation = {
            "source_name": "T2D Knowledge Portal",
            "source_file": source_file_rel,
            "chunk_id": f"ldsc:{phenotype}:{other_phenotype}",
            "method": "LDSC",
            "phenotype_pair": [phenotype, other_phenotype],
        }

        yield Chunk(
            chunk_id=f"ldsc:{phenotype}:{other_phenotype}",
            collection="ldsc_genetic_correlation",
            entity_type="genetic_correlation",
            title=f"LDSC genetic correlation: {phenotype} vs {other_phenotype}",
            content="\n".join(content_lines),
            metadata=metadata,
            citation=citation,
        )

    # Expose raw row count via function attribute for manifest reporting.
    chunk_ldsc_pairs.raw_row_count = raw_row_count  # type: ignore[attr-defined]
