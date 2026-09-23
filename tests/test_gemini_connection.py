from types import SimpleNamespace
from unittest.mock import Mock, patch
import json

import pytest

from src.rag.llm_engine import DEFAULT_GEMINI_MODEL, RealLLMEvaluator


def test_retired_model_falls_back_and_keeps_working_model():
    generate = Mock(side_effect=[RuntimeError("404 NOT_FOUND"), SimpleNamespace(text="OK")])
    evaluator = RealLLMEvaluator(
        api_key="test", model_name="gemini-2.5-flash",
        client=SimpleNamespace(models=SimpleNamespace(generate_content=generate)),
    )
    result = evaluator.test_connection()
    assert result["valid"] is True
    assert evaluator.model_name == DEFAULT_GEMINI_MODEL
    assert [call.kwargs["model"] for call in generate.call_args_list] == [
        "gemini-2.5-flash", DEFAULT_GEMINI_MODEL,
    ]


@pytest.mark.parametrize("error", ["429 RESOURCE_EXHAUSTED", "403 PERMISSION_DENIED"])
def test_connection_does_not_switch_models_on_quota_or_auth_error(error):
    generate = Mock(side_effect=RuntimeError(error))
    evaluator = RealLLMEvaluator(
        api_key="test", model_name="gemini-3.1-pro-preview",
        client=SimpleNamespace(models=SimpleNamespace(generate_content=generate)),
    )
    assert evaluator.test_connection()["valid"] is False
    generate.assert_called_once()


@pytest.mark.parametrize("recovers", [True, False])
def test_overload_retries_then_recovers_or_returns_no_score(recovers):
    overloaded = RuntimeError("503 UNAVAILABLE high demand")
    response = SimpleNamespace(text=json.dumps({
        "quality": "not_relevant", "justifying_quote": "",
        "is_self_contained": True, "is_link_farm": False,
    }))
    generate = Mock(side_effect=[overloaded, overloaded, response if recovers else overloaded])
    evaluator = RealLLMEvaluator(
        api_key="test", client=SimpleNamespace(models=SimpleNamespace(generate_content=generate)),
    )
    with patch("time.sleep") as sleep, patch("src.rag.llm_engine.random.uniform", return_value=0):
        result = evaluator.evaluate_evidence_with_llm(
            "17.2.4", "Partnerships", "Definition", 3,
            "Texte public de preuve", "https://example.org",
            methodology_question="Question officielle",
        )
    assert generate.call_count == 3
    assert [call.args[0] for call in sleep.call_args_list] == [4.0, 8.0]
    if recovers:
        assert "error" not in result
    else:
        assert result["error"] == "SERVICE_TEMPORAIREMENT_INDISPONIBLE"
        assert "the_points_earned" not in result


@pytest.mark.parametrize("error", ["429 RESOURCE_EXHAUSTED", "403 PERMISSION_DENIED"])
def test_evaluation_does_not_switch_models_on_quota_or_auth_error(error):
    generate = Mock(side_effect=RuntimeError(error))
    evaluator = RealLLMEvaluator(
        api_key="test", model_name="gemini-3.1-pro-preview",
        client=SimpleNamespace(models=SimpleNamespace(generate_content=generate)),
    )
    result = evaluator.evaluate_evidence_with_llm(
        "17.2.4", "Partnerships", "Definition", 3,
        "Texte public de preuve", "https://example.org",
        methodology_question="Question officielle",
    )
    assert result["error"] == "ERREUR_EXECUTION_LLM"
    generate.assert_called_once()
