import pytest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.evaluation.the_evaluator import THEEvidenceEvaluator

def test_evaluator_rejects_link_farm():
    evaluator = THEEvidenceEvaluator(target_year=2025)
    # Preuve consistant en une liste de liens sans descriptif suffisant
    link_farm_text = (
        "Voir nos partenaires sur les liens suivants : "
        "https://univ-constantine3.dz/p1 https://univ-constantine3.dz/p2 "
        "https://univ-constantine3.dz/p3 https://univ-constantine3.dz/p4"
    )
    result = evaluator.audit_evidence(
        indicator_id="17.2.1",
        indicator_definition="Relationships with regional NGOs and government for SDG policy",
        evidence_text=link_farm_text,
        source_url_or_path="https://univ-constantine3.dz/links",
        is_policy_indicator=False
    )
    assert result["is_link_farm"] is True
    assert result["quality"] == "not_relevant"
    assert any("REJET ÉLIMINATOIRE THE" in alert for alert in result["alerts"])

def test_evaluator_penalizes_attached_document_as_not_public():
    evaluator = THEEvidenceEvaluator(target_year=2025)
    local_file_path = "C:/Documents/UC3/Rapport_ODD_Interne_2025.pdf"
    content = (
        "En 2025, l'Université Constantine 3 Salah Boubnider a signé un partenariat formel avec la Direction "
        "de l'Environnement de Constantine pour la mise en œuvre de la politique ODD locale avec 200 participants."
    )
    result = evaluator.audit_evidence(
        indicator_id="17.2.1",
        indicator_definition="Relationships with regional NGOs and government for SDG policy",
        evidence_text=content,
        source_url_or_path=local_file_path,
        is_policy_indicator=False
    )
    assert result["is_public"] is False
    assert result["public_points"] == 0.0
    assert any("noté 'Non public'" in alert for alert in result["alerts"])

def test_evaluator_valid_public_specific():
    evaluator = THEEvidenceEvaluator(target_year=2025)
    public_url = "https://univ-constantine3.dz/colloque-odd-2025"
    content = (
        "En 2025, le Rectorat de l'Université Constantine 3 a organisé le dialogue intersectoriel ODD "
        "en présence de représentants du gouvernement et des ONG régionales avec 180 participants."
    )
    result = evaluator.audit_evidence(
        indicator_id="17.2.2",
        indicator_definition="Cross sectoral dialogue about SDGs involving government or NGOs",
        evidence_text=content,
        source_url_or_path=public_url,
        is_policy_indicator=False
    )
    assert result["is_public"] is True
    assert result["public_points"] == 1.0
    assert result["quality"] == "specific"
    assert result["total_points"] == 3.0  # 1.0 (statement) + 1.0 (specific) + 1.0 (public)
