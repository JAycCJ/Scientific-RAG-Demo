# CS-46 Evidence-Grounded Scientific RAG Assistant

This repository contains a reproducible offline RAG baseline for the approved
drug-discovery corpus. It covers corpus chunking, BM25/dense/hybrid retrieval,
context augmentation, deterministic evidence-grounded generation, claim-linked
citations, refusal, and end-to-end evaluation.

The default path requires no external LLM API and does not download an
embedding model. The development requirements include the FAISS library for
mock-vector tests, but not Torch or the Qwen model.

## Requirements

- Python 3.10 or newer (tested with Python 3.13.3)
- macOS, Linux, or Windows
- approximately 200 MB free space for the repository and BM25 index

## Reproduce the offline baseline

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
python scripts/build_bm25_index.py
python -m pytest -q
```

Windows PowerShell activation:

```powershell
.venv\Scripts\Activate.ps1
```

## Run the offline RAG demonstration

```bash
python scripts/query_rag_offline.py "What is the function of TCF7L2?"
```

The command prints the answer status, evidence-grounded answer, citation
records, limitations, validation result, and latency. It uses the deterministic
`OfflineEvidenceGenerator`; no API key is needed.

## Reproduce evaluation

```bash
python scripts/evaluate_bm25.py \
  --dev-set data/evaluation/retrieval_test.jsonl \
  --output-dir artifacts/evaluation/bm25_test_reproduced \
  --top-k 10 --report-ks 1 3 5 10
python scripts/build_rag_benchmark.py
python scripts/evaluate_rag_offline.py
```

Current local verification:

- 48 automated tests pass;
- answerable BM25 TargetHit@10: 87/90 (96.67%);
- answer/refuse status accuracy: 99%;
- unanswerable refusal accuracy: 10/10;
- structural citation correctness and completeness: 100%.

The citation figures validate references against supplied context. They are not
claims of 100% scientific or semantic answer correctness. See
[`docs/PROJECT_STATUS_AND_ROADMAP.md`](docs/PROJECT_STATUS_AND_ROADMAP.md).

## Optional dense and hybrid retrieval

Dense and hybrid retrieval are not required for the offline BM25 demonstration.
Install their larger dependencies separately:

```bash
python -m pip install -r requirements-embed.txt
python scripts/build_dense_index.py
python scripts/evaluate_dense.py \
  --dev-set data/evaluation/retrieval_test.jsonl \
  --output-dir artifacts/evaluation/dense_test_reproduced
python scripts/evaluate_hybrid.py \
  --dev-set data/evaluation/retrieval_test.jsonl \
  --output-dir artifacts/evaluation/hybrid_test_reproduced
```

The configured embedding model is `Qwen/Qwen3-Embedding-0.6B`. Building its
index can take a long time on a CPU or Apple laptop. Downloaded models and
generated indexes are intentionally excluded from Git.

## Repository guide

- Team update and file map: [`docs/TEAM_UPDATE_GUIDE.md`](docs/TEAM_UPDATE_GUIDE.md)
- Project status and roadmap: [`docs/PROJECT_STATUS_AND_ROADMAP.md`](docs/PROJECT_STATUS_AND_ROADMAP.md)
- Stage reports: [`reports/`](reports/)
- Retrieval configuration: [`config/retrieval.yaml`](config/retrieval.yaml)
- Generation configuration: [`config/generation.yaml`](config/generation.yaml)

## Data and security

The prototype operates only on the approved repository corpus. Never commit
`.env` files, API keys, client secrets, downloaded model weights, or generated
indexes. Confirm client approval before sending any corpus passage to an
external LLM provider.
