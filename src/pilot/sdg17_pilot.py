"""
Moteur Pilote ODD 17 - Partenariats pour la réalisation des objectifs
Université Constantine 3 (UC3) Salah Boubnider
Exécute l'analyse complète de l'ODD 17 obligatoire pour le classement THE 2027.
"""

from typing import Dict, Any, List
from src.methodology.the_2027_framework import THE2027Framework
from src.evaluation.the_evaluator import THEEvidenceEvaluator
from src.rag.retriever import UC3KnowledgeStore
from src.rag.extractor import UC3IndicatorExtractor
from src.rag.models import IndicatorFiche
from data.uc3_samples.sample_data_loader import load_uc3_sample_corpus

class SDG17PilotEngine:
    def __init__(self):
        self.framework = THE2027Framework()
        self.evaluator = THEEvidenceEvaluator(target_year=2025)
        self.store = UC3KnowledgeStore()
        self.extractor = UC3IndicatorExtractor(self.framework, self.evaluator)
        
        # Charger le corpus UC3
        load_uc3_sample_corpus(self.store)

    def run_pilot(self) -> Dict[str, Any]:
        """
        Exécute la collecte et l'évaluation pour l'ensemble des indicateurs de l'ODD 17.
        """
        sdg17_indicators = self.framework.get_indicators_for_sdg(17)
        fiches: List[IndicatorFiche] = []
        
        total_points = 0.0
        max_points = 0.0
        summary_counts = {
            "Information vérifiée": 0,
            "Inférence": 0,
            "Information à confirmer": 0,
            "Absence de donnée": 0
        }
        actions_counts = {
            "valider": 0,
            "publier": 0,
            "compléter": 0,
            "vérifier": 0,
            "rejeter": 0
        }

        for ind in sdg17_indicators:
            ind_id = ind["indicator_id"]
            ind_name = ind.get("name", "")
            
            # Recherche sémantique ciblée dans le corpus UC3
            query = f"{ind_name} {ind.get('definition', '')} Constantine 3 ODD développement durable"
            chunks = self.store.retrieve_relevant_chunks(query, top_k=2)
            
            # Extraction stricte sans hallucination
            fiche = self.extractor.extract_indicator_fiche(ind_id, chunks)
            fiches.append(fiche)

            total_points += fiche.the_points
            max_points += fiche.the_max_points
            summary_counts[fiche.status_category] = summary_counts.get(fiche.status_category, 0) + 1
            actions_counts[fiche.proposed_action] = actions_counts.get(fiche.proposed_action, 0) + 1

        overall_percentage = round((total_points / max_points * 100), 2) if max_points > 0 else 0.0

        return {
            "sdg_number": 17,
            "sdg_name": "SDG 17: Partnerships for the Goals",
            "is_mandatory": True,
            "target_year": 2025,
            "total_indicators": len(fiches),
            "total_points_earned": round(total_points, 2),
            "max_possible_points": round(max_points, 2),
            "sdg_completion_percentage": overall_percentage,
            "status_summary": summary_counts,
            "actions_summary": actions_counts,
            "fiches": [f.to_dict() for f in fiches]
        }
