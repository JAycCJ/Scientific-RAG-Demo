from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from augmentation.builder import ContextBuilder
from generation.aihubmix import AIHubMixGenerationError, AIHubMixGenerator
from generation.fallback import FallbackGenerator
from generation.offline import OfflineEvidenceGenerator
from generation.validator import validate_answer
from retrieval.service import RetrievalResponse
from tests.helpers import result


class FakeCompletions:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=value))]
        )


class FakeClient:
    def __init__(self, responses):
        self.completions = FakeCompletions(responses)
        self.chat = SimpleNamespace(completions=self.completions)


def context_for(question="What is the function of TCF7L2?"):
    response = RetrievalResponse(
        question=question,
        authorized_collections=["gene_info"],
        routed_collections=["gene_info"],
        effective_collections=["gene_info"],
        matched_rules=[],
        results=[result("gene:TCF7L2", "gene_info")],
        method="fixture",
        latency_s=0.0,
    )
    return ContextBuilder().build(response)


def payload(citation="gene:TCF7L2") -> str:
    return json.dumps(
        {
            "status": "answer",
            "answer": "TCF7L2 participates in Wnt signalling.",
            "claims": [
                {
                    "text": "TCF7L2 participates in Wnt signalling.",
                    "citations": [citation],
                }
            ],
            "limitations": [],
        }
    )


def test_aihubmix_returns_structured_cited_answer() -> None:
    context = context_for()
    fake = FakeClient([payload()])
    generator = AIHubMixGenerator(api_key="test-key", client=fake, repair_attempts=0)

    answer = generator.generate(context)

    assert answer.provider == "aihubmix"
    assert answer.claims[0].citations == ["gene:TCF7L2"]
    assert answer.citations[0]["chunk_id"] == "gene:TCF7L2"
    assert validate_answer(answer, context).valid
    assert fake.completions.calls == 1


def test_aihubmix_accepts_json_code_fence() -> None:
    context = context_for()
    fake = FakeClient([f"```json\n{payload()}\n```"])
    answer = AIHubMixGenerator(
        api_key="test-key", client=fake, repair_attempts=0
    ).generate(context)
    assert answer.status == "answer"


def test_aihubmix_does_not_call_api_for_refusal() -> None:
    context = context_for("Is my glucose a normal level for a patient?")
    fake = FakeClient([])
    answer = AIHubMixGenerator(
        api_key="test-key", client=fake, repair_attempts=0
    ).generate(context)
    assert answer.status == "refuse"
    assert fake.completions.calls == 0


def test_invalid_citation_falls_back_to_offline_generator() -> None:
    context = context_for()
    primary = AIHubMixGenerator(
        api_key="test-key", client=FakeClient([payload("gene:OTHER")]), repair_attempts=0
    )
    generator = FallbackGenerator(primary=primary, fallback=OfflineEvidenceGenerator())

    answer = generator.generate(context)

    assert answer.provider == "offline_evidence"
    assert answer.diagnostics["fallback_from"] == "aihubmix"
    assert validate_answer(answer, context).valid


def test_provider_error_falls_back_without_exposing_error_text() -> None:
    context = context_for()
    primary = AIHubMixGenerator(
        api_key="test-key", client=FakeClient([RuntimeError("secret value")]), repair_attempts=0
    )
    generator = FallbackGenerator(primary=primary, fallback=OfflineEvidenceGenerator())

    answer = generator.generate(context)

    assert answer.provider == "offline_evidence"
    assert answer.diagnostics["fallback_error_type"] == "AIHubMixGenerationError"
    assert "secret value" not in json.dumps(answer.diagnostics)


def test_invalid_json_raises_after_repair_budget() -> None:
    context = context_for()
    generator = AIHubMixGenerator(
        api_key="test-key", client=FakeClient(["not json"]), repair_attempts=0
    )
    with pytest.raises(AIHubMixGenerationError):
        generator.generate(context)


def test_empty_key_is_rejected() -> None:
    with pytest.raises(ValueError):
        AIHubMixGenerator(api_key="", client=FakeClient([]))
