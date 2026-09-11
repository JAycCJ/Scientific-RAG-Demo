from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from chunking.gene_chunker import chunk_genes
from chunking.ldsc_chunker import chunk_ldsc_pairs
from chunking.paths import load_paths
from chunking.phenotype_glossary import PhenotypeGlossary
from chunking.utils import parse_coding_sequence


class ChunkingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.glossary = PhenotypeGlossary(
            {
                "2hrI": {"label": "2-hour insulin (OGTT)", "category": "quantitative_trait"},
                "T2D": {"label": "Type 2 Diabetes", "category": "disease"},
            }
        )

    def test_load_paths_from_yaml(self) -> None:
        paths = load_paths(PROJECT_ROOT)
        self.assertTrue(paths.gene_file.exists())
        self.assertTrue(paths.ldsc_file.exists())
        self.assertEqual(paths.pipeline_version, "1.0.0")
        self.assertEqual(
            paths.gene_file,
            PROJECT_ROOT / "data" / "raw" / "gene_info" / "genes_function_info.json",
        )

    def test_parse_coding_sequence_standard(self) -> None:
        chromosome, start, end = parse_coding_sequence("10:114710009-114927437")
        self.assertEqual(chromosome, "10")
        self.assertEqual(start, 114710009)
        self.assertEqual(end, 114927437)

    def test_gene_chunk_complete_record(self) -> None:
        payload = {
            "source_base_url": "https://t2d.hugeamp.org/gene.html",
            "genes": {
                "TCF7L2": {
                    "gene": "TCF7L2",
                    "function_summary": "Wnt signaling",
                    "info": {
                        "alternative_names": ["TCF-4"],
                        "coding_sequence": "10:114710009-114927437",
                        "length_bp": 217429,
                        "assembly": "GRCh37",
                        "gene_sources": ["Ensembl"],
                        "ensembl_gene_id": "ENSG00000148737",
                        "hgnc_id": "11641",
                        "entrezgene": "6934",
                    },
                    "extracted_at_unix": 1767895499,
                    "uniprot_accession": "Q9NQB0",
                }
            },
        }
        chunk = next(chunk_genes(payload, Path("data/raw/gene_info/genes_function_info.json"), PROJECT_ROOT))
        self.assertEqual(chunk.chunk_id, "gene:TCF7L2")
        self.assertEqual(chunk.metadata["data_quality"], "complete")
        self.assertIn("Wnt signaling", chunk.content)

    def test_ldsc_pair_aggregation(self) -> None:
        ldsc_file = PROJECT_ROOT / "data" / "raw" / "ldsc" / "genetic_correlation" / "2hrl" / "2hrI.json"
        if not ldsc_file.exists():
            self.skipTest("LDSC sample file not available")

        chunks = list(chunk_ldsc_pairs(ldsc_file, self.glossary, PROJECT_ROOT))
        t2d_chunk = next(item for item in chunks if item.metadata["other_phenotype"] == "T2D")
        self.assertEqual(t2d_chunk.chunk_id, "ldsc:2hrI:T2D")
        self.assertEqual(len(t2d_chunk.metadata["results"]), 3)
        self.assertIn("Type 2 Diabetes", t2d_chunk.content)

    def test_manifest_exists_after_pipeline(self) -> None:
        manifest_path = PROJECT_ROOT / "artifacts" / "manifest.json"
        if not manifest_path.exists():
            self.skipTest("Manifest not generated yet")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertGreater(manifest["outputs"]["gene_info.chunks.jsonl"]["chunks"], 0)
        self.assertGreater(manifest["outputs"]["ldsc_2hrI.chunks.jsonl"]["chunks"], 0)


if __name__ == "__main__":
    unittest.main()
