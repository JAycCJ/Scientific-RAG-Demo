from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Chunk:
    chunk_id: str
    collection: str
    entity_type: str
    title: str
    content: str
    metadata: dict[str, Any]
    citation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChunkManifest:
    pipeline_version: str
    created_at: str
    sources: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
