import pytest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.methodology.the_2027_framework import THE2027Framework
from src.evaluation.the_evaluator import THEEvidenceEvaluator
from src.rag.extractor import UC3IndicatorExtractor

def test_zero_hallucination_on_missing_data():
    framework = THE2027Framework()
    evaluator = THEEvidenceEvaluator()
    extractor = UC3IndicatorExtractor(framework, evaluator)

    # Aucune donnée trouvée
    fiche = extractor.extract_indicator_fiche(
        indicator_id="17.4.4",
        retrieved_chunks=[]
    )
    
    assert fiche.status_category == "Absence de donnée"
    assert fiche.the_points == 0.0
    assert "Aucune mention ou preuve" in fiche.information_found
    assert fiche.proposed_action == "compléter"
    assert fiche.confidence == "faible"

def test_verified_information_extraction():
    framework = THE2027Framework()
    evaluator = THEEvidenceEvaluator()
    extractor = UC3IndicatorExtractor(framework, evaluator)

    chunks = [{
        "text": "L'Université Constantine 3 Salah Boubnider a réuni en mai 2025 plus de 180 délégués ministériels et ONG pour un dialogue intersectoriel ODD.",
        "source_url_or_path": "https://univ-constantine3.dz/dialogue-2025",
        "entity": "Rectorat UC3",
        "source_type": "WEB_PAGE",
        "is_public": True,
        "date": "2025-05-18"
    }]

    fiche = extractor.extract_indicator_fiche(
        indicator_id="17.2.2",
        retrieved_chunks=chunks
    )

    assert fiche.status_category == "Information vérifiée"
    assert fiche.confidence == "élevée"
    assert fiche.year == 2025
    assert fiche.publicity == "publique"
    assert fiche.the_points == 3.0
