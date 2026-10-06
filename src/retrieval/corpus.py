from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chunking.utils import file_sha256, load_jsonl
from retrieval.config import ChunkSource, RetrievalConfig
from retrieval.schema import ChunkRecord


@dataclass
class LoadedCorpus:
    records: list[ChunkRecord]
    chunk_hashes: dict[str, str]
    collection_counts: dict[str, int]


def load_manifest_counts(manifest_file: Path) -> dict[str, int]:
    with manifest_file.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    counts: dict[str, int] = {}
    filename_to_collection = {
        "gene_info.chunks.jsonl": "gene_info",
        "ldsc_2hrI.chunks.jsonl": "ldsc_genetic_correlation",
        "gene_association_common_2hrG.chunks.jsonl": "gene_association_common",
        "gene_association_rare_2hrG.chunks.jsonl": "gene_association_rare",
    }
    for filename, payload in manifest.get("outputs", {}).items():
        collection = filename_to_collection.get(filename)
        if collection:
            counts[collection] = int(payload["chunks"])
    return counts


def load_corpus(
    sources: list[ChunkSource] | tuple[ChunkSource, ...],
    *,
    manifest_file: Path | None = None,
    expected_total: int | None = 41103,
) -> LoadedCorpus:
    records: list[ChunkRecord] = []
    chunk_hashes: dict[str, str] = {}
    collection_counts: dict[str, int] = {}
    seen_ids: set[str] = set()

    for source in sources:
        if not source.path.exists():
            raise FileNotFoundError(f"Chunk artifact not found: {source.path}")
        chunk_hashes[source.path.as_posix()] = file_sha256(source.path)
        count = 0
        for payload in load_jsonl(source.path):
            record = ChunkRecord.from_dict(payload)
            if record.collection != source.collection:
                raise ValueError(
                    f"Collection mismatch in {source.path}: {record.collection} != {source.collection}"
                )
            if record.chunk_id in seen_ids:
                raise ValueError(f"Duplicate chunk_id: {record.chunk_id}")
            seen_ids.add(record.chunk_id)
            records.append(record)
            count += 1
        collection_counts[source.collection] = count

    if expected_total is not None and len(records) != expected_total:
        raise ValueError(f"Expected {expected_total} chunks, loaded {len(records)}")

    if manifest_file and manifest_file.exists():
        expected = load_manifest_counts(manifest_file)
        for collection, count in expected.items():
            actual = collection_counts.get(collection)
            if actual != count:
                raise ValueError(
                    f"Manifest count mismatch for {collection}: expected {count}, got {actual}"
                )

    return LoadedCorpus(
        records=records,
        chunk_hashes=chunk_hashes,
        collection_counts=collection_counts,
    )


def load_corpus_from_config(config: RetrievalConfig, *, expected_total: int | None = 41103) -> LoadedCorpus:
    return load_corpus(
        config.chunk_sources,
        manifest_file=config.manifest_file,
        expected_total=expected_total,
    )


def corpus_by_id(records: list[ChunkRecord]) -> dict[str, ChunkRecord]:
    return {record.chunk_id: record for record in records}


def metadata_matches(record: ChunkRecord, filters: dict[str, Any] | None) -> bool:
    if not filters:
        return True
    for key, expected in filters.items():
        actual = record.metadata.get(key, getattr(record, key, None))
        if actual != expected:
            return False
    return True
