from __future__ import annotations

from augmentation.schema import ContextPackage, EvidencePassage
from generation.schema import Claim, GeneratedAnswer


def _claim_text(p: EvidencePassage) -> str:
    m = p.metadata
    if p.collection == "ldsc_genetic_correlation":
        return (
            f"{p.title}: Mixed-ancestry rg={m.get('mixed_rg')} and "
            f"p={m.get('mixed_pvalue')}."
        )
    if p.collection == "gene_association_rare":
        return (
            f"{m.get('gene')} has rare-variant evidence for {m.get('phenotype_label')}: "
            f"p={m.get('pValue')}, beta={m.get('beta')}, significant={m.get('is_significant')}."
        )
    if p.collection == "gene_association_common":
        return (
            f"{m.get('gene')} has common-variant evidence for {m.get('phenotype_label')} "
            f"with bf_common={m.get('bf_common')} and evidence tier {m.get('evidence_tier')}."
        )
    function_line = next(
        (line.removeprefix("Function: ") for line in p.content.splitlines() if line.startswith("Function: ")),
        "Function information is not available in the approved corpus.",
    )
    return f"{p.title}: {function_line}"


class OfflineEvidenceGenerator:
    provider = "offline_evidence"
    prompt_policy_version = "1.0.0"

    def generate(self, context: ContextPackage) -> GeneratedAnswer:
        if context.evidence_status == "refuse":
            text = "I cannot answer this question from the authorized approved corpus."
            return GeneratedAnswer(
                status="refuse",
                answer=text,
                claims=[],
                citations=[],
                limitations=context.limitations,
            )
        claims = [Claim(text=_claim_text(p), citations=[p.chunk_id]) for p in context.passages]
        prefix = "The available evidence is limited. " if context.evidence_status == "qualified" else ""
        answer = prefix + " ".join(claim.text for claim in claims)
        citations = [context.citation_registry[cid] for claim in claims for cid in claim.citations]
        return GeneratedAnswer(
            status=context.evidence_status,
            answer=answer,
            claims=claims,
            citations=citations,
            limitations=context.limitations,
            diagnostics={"claim_count": len(claims)},
        )
