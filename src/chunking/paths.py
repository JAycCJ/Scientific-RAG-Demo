from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ProjectPaths:
    project_root: Path
    gene_file: Path
    ldsc_file: Path
    glossary_file: Path
    chunks_dir: Path
    manifest_file: Path
    pipeline_version: str
    config_file: Path


def _resolve(project_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (project_root / path).resolve()


def load_paths(
    project_root: Path,
    config_file: Path | None = None,
) -> ProjectPaths:
    config_path = (config_file or project_root / "config" / "paths.yaml").resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Paths config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    root_value = data.get("project_root", ".")
    if root_value == ".":
        resolved_root = project_root.resolve()
    else:
        resolved_root = _resolve(project_root, root_value)

    raw = data["raw"]
    artifacts = data["artifacts"]
    config = data["config"]

    return ProjectPaths(
        project_root=resolved_root,
        gene_file=_resolve(resolved_root, raw["gene_info"]),
        ldsc_file=_resolve(resolved_root, raw["ldsc_2hri"]),
        glossary_file=_resolve(resolved_root, config["phenotype_glossary"]),
        chunks_dir=_resolve(resolved_root, artifacts["chunks_dir"]),
        manifest_file=_resolve(resolved_root, artifacts["manifest"]),
        pipeline_version=str(data.get("pipeline_version", "1.0.0")),
        config_file=config_path,
    )
