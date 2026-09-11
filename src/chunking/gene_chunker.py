from __future__ import annotations

from pathlib import Path
from typing import Iterator

from chunking.schema import Chunk
from chunking.utils import (
    format_optional,
    infer_gene_data_quality,
    parse_coding_sequence,
    relative_source_path,
    unix_to_iso8601,
)


def chunk_genes(
    genes_payload: dict,
    source_file: Path,
    project_root: Path,
) -> Iterator[Chunk]:
    source_base_url = genes_payload.get("source_base_url", "https://t2d.hugeamp.org/gene.html")
    genes = genes_payload.get("genes", {})
    source_file_rel = relative_source_path(source_file, project_root)

    for symbol, record in genes.items():
        info = record.get("info") or {}
        chromosome, start, end = parse_coding_sequence(info.get("coding_sequence"))
        function_summary = record.get("function_summary")
        has_function_summary = function_summary is not None
        data_quality = infer_gene_data_quality(record)
        alternative_names = info.get("alternative_names") or []

        location_parts = []
        if chromosome and start is not None and end is not None:
            location_parts.append(f"chr{chromosome}:{start}-{end}")
        elif info.get("coding_sequence"):
            location_parts.append(str(info.get("coding_sequence")))
        else:
            location_parts.append("unknown")

        assembly = format_optional(info.get("assembly"), "unknown")
        location_text = f"{' '.join(location_parts)} ({assembly})"

        content_lines = [
            f"Gene: {symbol}",
            f"Alternative names: {', '.join(alternative_names) if alternative_names else 'N/A'}",
            (
                f"Function: {function_summary}"
                if has_function_summary
                else "Function: Not available in the approved corpus."
            ),
            f"Genomic location: {location_text}",
            f"Gene length: {format_optional(info.get('length_bp'), 'unknown')} bp",
            (
                "Database identifiers: "
                f"Ensembl {format_optional(info.get('ensembl_gene_id'))}, "
                f"HGNC {format_optional(info.get('hgnc_id'))}, "
                f"Entrez {format_optional(info.get('entrezgene'))}, "
                f"UniProt {format_optional(record.get('uniprot_accession'))}"
            ),
            f"Data sources: {', '.join(info.get('gene_sources') or []) or 'N/A'}",
            (
                "Provenance: Extracted from T2D Knowledge Portal "
                f"({source_base_url}), extracted_at={unix_to_iso8601(record.get('extracted_at_unix'))}"
            ),
        ]

        if record.get("error"):
            content_lines.append(f"Data quality note: {record['error']}")

        metadata = {
            "entity_type": "gene",
            "gene_symbol": symbol,
            "alternative_names": alternative_names,
            "ensembl_gene_id": info.get("ensembl_gene_id"),
            "hgnc_id": info.get("hgnc_id"),
            "entrezgene": info.get("entrezgene"),
            "uniprot_accession": record.get("uniprot_accession"),
            "chromosome": chromosome,
            "start": start,
            "end": end,
            "assembly": info.get("assembly"),
            "length_bp": info.get("length_bp"),
            "has_function_summary": has_function_summary,
            "data_quality": data_quality,
            "source_base_url": source_base_url,
            "extracted_at_unix": record.get("extracted_at_unix"),
            "source_file": source_file_rel,
        }

        citation = {
            "source_name": "T2D Knowledge Portal",
            "source_url": source_base_url,
            "source_file": source_file_rel,
            "chunk_id": f"gene:{symbol}",
            "extracted_at_unix": record.get("extracted_at_unix"),
        }

        yield Chunk(
            chunk_id=f"gene:{symbol}",
            collection="gene_info",
            entity_type="gene",
            title=f"Gene {symbol}",
            content="\n".join(content_lines),
            metadata=metadata,
            citation=citation,
        )
