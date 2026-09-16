# Raw source data (read-only)

Place client-provided source files here. Do not modify files in this directory.
Update `config/paths.yaml` when adding or relocating data sources.

## Layout (by data type)

- `gene_info/genes_function_info.json` — gene function and annotation (T2D Knowledge Portal)
- `reference/gene_id_map/genes.jsonl` — gene symbol / Ensembl ↔ genomic coordinates (HuGE export)
- `ldsc/genetic_correlation/2hrI/2hrI.json` — LDSC genetic correlation (anchor phenotype 2hrI)
- `gene_association/common/2hrG/2hrG.common.jsonl` — common-variant gene–phenotype evidence for 2hrG (HuGE)
- `gene_association/rare/2hrG/2hrG.rare.jsonl` — rare-variant gene-level association for 2hrG (HuGE)

HuGE refers to the T2D Portal export module; paths here are organized by analysis type, not portal folder names.

Pipeline outputs are written to `artifacts/`.
