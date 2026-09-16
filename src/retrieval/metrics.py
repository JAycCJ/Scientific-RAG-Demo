from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


def _grade2_ids(example: dict[str, Any]) -> list[str]:
    return [
        item["chunk_id"]
        for item in example.get("relevance_judgments", [])
        if int(item.get("grade", 0)) >= 2
    ]


def target_hit_at_k(retrieved_ids: list[str], gold_ids: Iterable[str], k: int) -> float:
    gold = set(gold_ids)
    if not gold:
        return 0.0
    return 1.0 if gold.intersection(retrieved_ids[:k]) else 0.0


def mrr_at_k(retrieved_ids: list[str], gold_ids: Iterable[str], k: int) -> float:
    gold = set(gold_ids)
    for rank, chunk_id in enumerate(retrieved_ids[:k], start=1):
        if chunk_id in gold:
            return 1.0 / rank
    return 0.0


def router_scores(predicted: list[str], target: list[str]) -> dict[str, float]:
    predicted_set = set(predicted)
    target_set = set(target)
    if not predicted_set and not target_set:
        return {"exact_set": 1.0, "precision": 1.0, "recall": 1.0}
    intersection = predicted_set & target_set
    precision = len(intersection) / len(predicted_set) if predicted_set else 0.0
    recall = len(intersection) / len(target_set) if target_set else 0.0
    exact = 1.0 if predicted_set == target_set else 0.0
    return {"exact_set": exact, "precision": precision, "recall": recall}


def aggregate_dev_metrics(
    rows: list[dict[str, Any]],
    report_ks: tuple[int, ...],
    view_key: str,
) -> dict[str, Any]:
    max_k = max(report_ks)
    hits = {k: [] for k in report_ks}
    mrrs: list[float] = []
    router_exact: list[float] = []
    router_p: list[float] = []
    router_r: list[float] = []
    by_type: dict[str, dict[str, list[float]]] = defaultdict(lambda: {**{f"hit@{k}": [] for k in report_ks}, "mrr": []})

    for row in rows:
        gold = _grade2_ids(row["example"])
        retrieved = [item["chunk_id"] for item in row[view_key]["results"]]
        query_type = row["example"].get("query_type", "unknown")
        mrr = mrr_at_k(retrieved, gold, max_k)
        mrrs.append(mrr)
        by_type[query_type]["mrr"].append(mrr)
        for k in report_ks:
            hit = target_hit_at_k(retrieved, gold, k)
            hits[k].append(hit)
            by_type[query_type][f"hit@{k}"].append(hit)

        target_collections = row["example"].get("target_collections") or []
        route_metrics = router_scores(row["route"]["collections"], target_collections)
        router_exact.append(route_metrics["exact_set"])
        router_p.append(route_metrics["precision"])
        router_r.append(route_metrics["recall"])

    def mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    sliced = {}
    for query_type, values in sorted(by_type.items()):
        sliced[query_type] = {
            **{f"TargetHit@{k}": round(mean(values[f"hit@{k}"]), 4) for k in report_ks},
            f"MRR@{max_k}": round(mean(values["mrr"]), 4),
            "n": len(values["mrr"]),
        }

    return {
        "n": len(rows),
        "metrics": {
            **{f"TargetHit@{k}": round(mean(hits[k]), 4) for k in report_ks},
            f"MRR@{max_k}": round(mean(mrrs), 4),
        },
        "router": {
            "exact_set_accuracy": round(mean(router_exact), 4),
            "collection_precision": round(mean(router_p), 4),
            "collection_recall": round(mean(router_r), 4),
        },
        "by_query_type": sliced,
        "labeling_note": (
            "TargetHit@k is 1 if any grade-2 gold chunk_id appears in the top-k results. "
            "This is not pooled corpus-level Recall."
        ),
    }
