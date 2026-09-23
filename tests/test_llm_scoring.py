"""The provider's numeric answer must never override local scoring rules."""

import json
import sys
import types
from unittest.mock import patch
import pytest

from src.rag.llm_engine import RealLLMEvaluator


def _mock_genai_client(response_data: dict):
    """Helper to mock google-genai Client returning specified JSON dictionary."""
    class FakeClient:
        def __init__(self, api_key):
            self.models = self

        def generate_content(self, **kwargs):
            return types.SimpleNamespace(text=json.dumps(response_data))

    google = types.ModuleType("google")
    genai = types.ModuleType("google.genai")
    genai.Client = FakeClient
    genai.types = types.SimpleNamespace(GenerateContentConfig=lambda **kw: kw)
    google.genai = genai
    return google, genai


def test_irrelevant_evidence_cannot_receive_provider_points():
    mock_data = {
        "quality": "not_relevant",
        "justifying_quote": "",
        "is_self_contained": True,
        "is_link_farm": False,
        "the_points_earned": 3,
        "status_category": "Information vérifiée",
    }
    google, genai = _mock_genai_client(mock_data)
    with patch.dict(sys.modules, {"google": google, "google.genai": genai}):
        evaluator = RealLLMEvaluator(api_key="test")
        result = evaluator.evaluate_evidence_with_llm(
            "17.2.4", "Partnerships", "Summary", 3,
            "Un horaire de transport sans rapport", "https://univ-constantine3.dz/x",
            methodology_question="Exact question from the 2027 PDF", source_verified=True,
        )
    assert result["the_points_earned"] == 0
    assert result["status_category"] == "Absence de donnée"
    assert result["statement_points"] == 0.0
    assert result["evidence_points"] == 0.0
    assert result["public_points"] == 0.0


def test_specific_evidence_scraped_public_web_page():
    evidence = "L'Université Constantine 3 a alloué en 2025 un budget de 5 millions DZD pour les étudiants boursiers."
    mock_data = {
        "quality": "specific",
        "justifying_quote": "L'Université Constantine 3 a alloué en 2025 un budget de 5 millions DZD",
        "is_self_contained": True,
        "is_link_farm": False,
        "detected_year": 2025,
        "uc3_entity": "Rectorat",
    }
    google, genai = _mock_genai_client(mock_data)
    with patch.dict(sys.modules, {"google": google, "google.genai": genai}):
        evaluator = RealLLMEvaluator(api_key="test")
        result = evaluator.evaluate_evidence_with_llm(
            indicator_id="1.3.1",
            indicator_name="Admission target",
            indicator_definition="Summary",
            max_points=3.0,
            evidence_text=evidence,
            source_url_or_path="https://univ-constantine3.dz/bourses-2025",
            methodology_question="Exact question from PDF 2027",
            source_verified=True,
            source_is_attachment=False,
        )
    assert result["quality"] == "specific"
    assert result["is_public"] is True
    assert result["statement_points"] == 1.0
    assert result["evidence_points"] == 1.0
    assert result["public_points"] == 1.0
    assert result["the_points_earned"] == 3.0
    assert result["the_percentage"] == 100.0


def test_general_evidence_scoring():
    evidence = "L'université dispose d'une politique générale de soutien financier pour ses étudiants défavorisés."
    mock_data = {
        "quality": "general",
        "justifying_quote": "L'université dispose d'une politique générale de soutien financier",
        "is_self_contained": True,
        "is_link_farm": False,
        "detected_year": 2025,
    }
    google, genai = _mock_genai_client(mock_data)
    with patch.dict(sys.modules, {"google": google, "google.genai": genai}):
        evaluator = RealLLMEvaluator(api_key="test")
        result = evaluator.evaluate_evidence_with_llm(
            indicator_id="1.3.1",
            indicator_name="Admission target",
            indicator_definition="Summary",
            max_points=3.0,
            evidence_text=evidence,
            source_url_or_path="https://univ-constantine3.dz/general",
            methodology_question="Exact question from PDF 2027",
            source_verified=True,
            source_is_attachment=False,
        )
    assert result["quality"] == "general"
    assert result["statement_points"] == 1.0
    assert result["evidence_points"] == 0.5
    assert result["public_points"] == 1.0
    assert result["the_points_earned"] == 2.5


def test_attachment_receives_zero_public_points():
    evidence = "PV du Conseil d'Administration du 15 janvier 2025 approuvant la charte d'égalité des chances."
    mock_data = {
        "quality": "specific",
        "justifying_quote": "PV du Conseil d'Administration du 15 janvier 2025 approuvant la charte",
        "is_self_contained": True,
        "is_link_farm": False,
        "detected_year": 2025,
    }
    google, genai = _mock_genai_client(mock_data)
    with patch.dict(sys.modules, {"google": google, "google.genai": genai}):
        evaluator = RealLLMEvaluator(api_key="test")
        result = evaluator.evaluate_evidence_with_llm(
            indicator_id="10.3.1",
            indicator_name="Non-discriminatory charter",
            indicator_definition="Summary",
            max_points=3.0,
            evidence_text=evidence,
            source_url_or_path="PV_Conseil_2025.pdf",
            methodology_question="Exact question from PDF 2027",
            source_verified=True,
            source_is_attachment=True,
        )
    assert result["quality"] == "specific"
    assert result["is_public"] is False
    assert result["statement_points"] == 1.0
    assert result["evidence_points"] == 1.0
    assert result["public_points"] == 0.0
    assert result["the_points_earned"] == 2.0


def test_pasted_text_declared_url_receives_zero_public_points():
    evidence = "Déclaration interne : UC3 organise chaque mois un atelier d'accompagnement des primo-arrivants."
    mock_data = {
        "quality": "specific",
        "justifying_quote": "UC3 organise chaque mois un atelier d'accompagnement des primo-arrivants",
        "is_self_contained": True,
        "is_link_farm": False,
        "detected_year": 2025,
    }
    google, genai = _mock_genai_client(mock_data)
    with patch.dict(sys.modules, {"google": google, "google.genai": genai}):
        evaluator = RealLLMEvaluator(api_key="test")
        result = evaluator.evaluate_evidence_with_llm(
            indicator_id="4.3.5",
            indicator_name="Lifelong learning",
            indicator_definition="Summary",
            max_points=3.0,
            evidence_text=evidence,
            source_url_or_path="https://univ-constantine3.dz/declared-only",
            methodology_question="Exact question from PDF 2027",
            source_verified=False,
            source_is_attachment=False,
        )
    assert result["is_public"] is False
    assert result["public_points"] == 0.0
    assert result["statement_points"] == 1.0
    assert result["evidence_points"] == 1.0
    assert result["the_points_earned"] == 2.0


def test_hallucinated_verbatim_quote_fails():
    evidence = "Texte réel : L'université a installé 100 panneaux solaires sur le campus en mars 2025."
    mock_data = {
        "quality": "specific",
        "justifying_quote": "Citation complètement hallucinée et absente du texte d'origine",
        "is_self_contained": True,
        "is_link_farm": False,
    }
    google, genai = _mock_genai_client(mock_data)
    with patch.dict(sys.modules, {"google": google, "google.genai": genai}):
        evaluator = RealLLMEvaluator(api_key="test")
        result = evaluator.evaluate_evidence_with_llm(
            indicator_id="7.2.1",
            indicator_name="Clean energy",
            indicator_definition="Summary",
            max_points=3.0,
            evidence_text=evidence,
            source_url_or_path="https://univ-constantine3.dz/energie",
            methodology_question="Exact question from PDF 2027",
            source_verified=True,
        )
    assert "error" in result
    assert "Citation justificative non présente mot pour mot" in result["message"]


def test_policy_review_bonus_applied_only_when_eligible():
    evidence = "Politique institutionnelle de gestion des déchets, adoptée en 2020 et révisée en novembre 2024."
    mock_data = {
        "quality": "specific",
        "justifying_quote": "Politique institutionnelle de gestion des déchets, adoptée en 2020 et révisée en novembre 2024",
        "is_self_contained": True,
        "is_link_farm": False,
        "policy_reviewed_2022_2026": True,
        "detected_year": 2024,
    }
    google, genai = _mock_genai_client(mock_data)
    with patch.dict(sys.modules, {"google": google, "google.genai": genai}):
        evaluator = RealLLMEvaluator(api_key="test")
        # 1. Avec bonus éligible
        res_bonus = evaluator.evaluate_evidence_with_llm(
            indicator_id="12.2.1",
            indicator_name="Ethical sourcing policy",
            indicator_definition="Summary",
            max_points=4.0,
            evidence_text=evidence,
            source_url_or_path="https://univ-constantine3.dz/politique-dechets",
            methodology_question="Have a policy... Up to four points based on... created or reviewed 2022-2026",
            is_policy_bonus_eligible=True,
            source_verified=True,
        )
        assert res_bonus["policy_bonus_points"] == 1.0
        assert res_bonus["the_max_points"] == 4.0
        assert res_bonus["the_points_earned"] == 4.0  # 1 (dec) + 1 (ev) + 1 (pub) + 1 (bonus)

        # 2. Sans bonus éligible (indicateur standard à 3 points)
        res_no_bonus = evaluator.evaluate_evidence_with_llm(
            indicator_id="12.3.1",
            indicator_name="Standard activity",
            indicator_definition="Summary",
            max_points=3.0,
            evidence_text=evidence,
            source_url_or_path="https://univ-constantine3.dz/activite",
            methodology_question="Standard question without policy bonus",
            is_policy_bonus_eligible=False,
            source_verified=True,
        )
        assert res_no_bonus["policy_bonus_points"] == 0.0
        assert res_no_bonus["the_max_points"] == 3.0
        assert res_no_bonus["the_points_earned"] == 3.0


def test_link_farm_rejection():
    evidence = "Consultez nos liens : [Lien 1](https://a.com), [Lien 2](https://b.com), [Lien 3](https://c.com)"
    mock_data = {
        "quality": "specific",
        "justifying_quote": "Consultez nos liens",
        "is_self_contained": False,
        "is_link_farm": True,
    }
    google, genai = _mock_genai_client(mock_data)
    with patch.dict(sys.modules, {"google": google, "google.genai": genai}):
        evaluator = RealLLMEvaluator(api_key="test")
        result = evaluator.evaluate_evidence_with_llm(
            indicator_id="17.2.1",
            indicator_name="Relationships",
            indicator_definition="Summary",
            max_points=3.0,
            evidence_text=evidence,
            source_url_or_path="https://univ-constantine3.dz/links",
            methodology_question="Exact question from PDF 2027",
            source_verified=True,
        )
    assert result["quality"] == "not_relevant"
    assert result["the_points_earned"] == 0.0
    assert result["status_category"] == "Absence de donnée"


def test_missing_methodology_question_returns_error():
    evaluator = RealLLMEvaluator(api_key="test")
    res = evaluator.evaluate_evidence_with_llm(
        indicator_id="1.3.1",
        indicator_name="Admission target",
        indicator_definition="Summary",
        max_points=3.0,
        evidence_text="Texte de test",
        source_url_or_path="https://univ-constantine3.dz",
        methodology_question="",
    )
    assert res.get("error") == "METHODOLOGIE_MANQUANTE"


def test_unconfigured_api_key_returns_error():
    evaluator = RealLLMEvaluator(api_key="")
    res = evaluator.evaluate_evidence_with_llm(
        indicator_id="1.3.1",
        indicator_name="Admission target",
        indicator_definition="Summary",
        max_points=3.0,
        evidence_text="Texte de test",
        source_url_or_path="https://univ-constantine3.dz",
        methodology_question="Question",
    )
    assert res.get("error") == "CLÉ_API_MANQUANTE"


def test_bilingual_fields_generation():
    evidence = "Le Conseil Scientifique de l'UC3 a validé en 2025 un programme de bourses d'excellence."
    mock_data = {
        "quality": "specific",
        "justifying_quote": "Le Conseil Scientifique de l'UC3 a validé en 2025",
        "is_self_contained": True,
        "is_link_farm": False,
        "detected_year": 2025,
        "information_found": "Validation d'un programme de bourses en 2025.",
        "english_summary_for_the": "In 2025, Constantine 3 University approved an excellence scholarship program.",
        "quote_english_translation": "The Scientific Council of UC3 approved in 2025",
    }
    google, genai = _mock_genai_client(mock_data)
    with patch.dict(sys.modules, {"google": google, "google.genai": genai}):
        evaluator = RealLLMEvaluator(api_key="test")
        result = evaluator.evaluate_evidence_with_llm(
            indicator_id="1.3.1",
            indicator_name="Admission target",
            indicator_definition="Summary",
            max_points=3.0,
            evidence_text=evidence,
            source_url_or_path="https://univ-constantine3.dz/bourses",
            methodology_question="Exact question from PDF 2027",
            source_verified=True,
        )
    assert result["quality"] == "specific"
    assert "english_summary_for_the" in result
    assert "scholarship program" in result["english_summary_for_the"]
    assert "quote_english_translation" in result
    assert "Scientific Council" in result["quote_english_translation"]

