"""
Moteur d'Extraction Zéro-Hallucination & Générateur de Fiches d'Indicateurs UC3
Conformité stricte aux exigences institutionnelles :
- Aucune extrapolation ou supposition
- Catégorisation formelle : Information vérifiée, Inférence, Information à confirmer, Absence de donnée
- Analyse contradictoire multi-sources
- Simulation de l'évaluation THE LLM
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import re

from src.rag.models import IndicatorFiche
from src.evaluation.the_evaluator import THEEvidenceEvaluator
from src.methodology.the_2027_framework import THE2027Framework

class UC3IndicatorExtractor:
    def __init__(self, framework: THE2027Framework, evaluator: THEEvidenceEvaluator):
        self.framework = framework
        self.evaluator = evaluator

    def extract_indicator_fiche(
        self,
        indicator_id: str,
        retrieved_chunks: List[Dict[str, Any]],
        manual_declaration: Optional[Dict[str, Any]] = None
    ) -> IndicatorFiche:
        """
        Extrait et construit la fiche réglementaire pour un indicateur donné.
        Si aucune preuve n'est trouvée, produit rigoureusement une fiche "Absence de donnée".
        """
        ind_meta = self.framework.get_indicator(indicator_id) or {}
        ind_title = ind_meta.get("name", f"Indicateur {indicator_id}")
        ind_definition = ind_meta.get("definition", ind_title)
        is_policy = ind_meta.get("reviewed_policy_bonus", False) or "policy" in ind_title.lower()

        # Si aucune source trouvée dans les documents UC3
        if not retrieved_chunks and not manual_declaration:
            return IndicatorFiche(
                odd_indicator=indicator_id,
                indicator_title=ind_title,
                methodological_requirement=ind_definition,
                information_found="Aucune mention ou preuve correspondante trouvée dans le corpus institutionnel indexé de l'UC3.",
                year=None,
                source_exact="N/A (Corpus indexé UC3)",
                consultation_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                justifying_quote="",
                uc3_entity="Non identifiée",
                quality="non_pertinente",
                publicity="interne",
                confidence="faible",
                gap_or_alert="Absence totale de données documentées pour cet indicateur dans les archives et le portail web.",
                proposed_action="compléter",
                status_category="Absence de donnée",
                the_points=0.0,
                the_max_points=4.0 if is_policy else 3.0,
                the_percentage=0.0,
                is_self_contained=False,
                is_link_farm_rejected=False
            )

        # Sélection de la meilleure source parmi les chunks récupérés
        best_chunk = retrieved_chunks[0] if retrieved_chunks else {}
        evidence_text = best_chunk.get("text", "")
        source_url_or_path = best_chunk.get("source_url_or_path", "")
        entity = best_chunk.get("entity", "Université Constantine 3")
        source_type = best_chunk.get("source_type", "DOC")

        # Détection d'éventuelles contradictions si plusieurs chunks fournissent des dates ou chiffres divergents
        contradictions = []
        if len(retrieved_chunks) > 1:
            years_found = set()
            for c in retrieved_chunks:
                ys = re.findall(r"\b(20[12][0-9])\b", c.get("text", ""))
                if ys:
                    years_found.update(ys)
            if len(years_found) > 1:
                contradictions.append(f"Contradiction temporelle détectée entre les sources : années mentionnées {sorted(list(years_found))}")

        # Audit par le simulateur THE LLM
        eval_result = self.evaluator.audit_evidence(
            indicator_id=indicator_id,
            indicator_definition=ind_definition,
            evidence_text=evidence_text,
            source_url_or_path=source_url_or_path,
            is_policy_indicator=is_policy
        )

        detected_year = eval_result.get("detected_year")
        quality = eval_result.get("quality", "non_pertinente")
        is_public = eval_result.get("is_public", False)
        is_link_farm = eval_result.get("is_link_farm", False)

        # Détermination de l'information trouvée (synthèse factuelle fidèle)
        # On extrait la première phrase clé ou l'énoncé du fait sans invention
        first_meaningful_sentence = ""
        for line in evidence_text.split("\n"):
            line_str = line.strip()
            if len(line_str) > 30 and not line_str.startswith("http"):
                first_meaningful_sentence = line_str
                break
        
        info_found = first_meaningful_sentence if first_meaningful_sentence else evidence_text[:200]

        # Détermination stricte du statut (Information vérifiée, Inférence, Information à confirmer, Absence de donnée)
        if is_link_farm:
            status_category = "Absence de donnée"
            confidence = "faible"
            action = "rejeter"
        elif quality == "specific" and detected_year == 2025 and is_public:
            status_category = "Information vérifiée"
            confidence = "élevée"
            action = "valider"
        elif quality == "specific" and not is_public:
            status_category = "Information à confirmer"
            confidence = "moyenne"
            action = "publier"  # Doit être publié sur web UC3
        elif quality == "general":
            status_category = "Inférence"
            confidence = "moyenne"
            action = "compléter"
        else:
            status_category = "Information à confirmer"
            confidence = "faible"
            action = "vérifier"

        # Concaténation des alertes
        all_alerts = eval_result.get("alerts", []) + contradictions
        gap_alert_str = " | ".join(all_alerts) if all_alerts else "Aucune non-conformité détectée."

        # Extrait justificatif verbatim (limité à 400 caractères de citation exacte)
        quote = evidence_text[:400] + ("..." if len(evidence_text) > 400 else "")

        return IndicatorFiche(
            odd_indicator=indicator_id,
            indicator_title=ind_title,
            methodological_requirement=ind_definition,
            information_found=info_found,
            year=detected_year,
            source_exact=source_url_or_path,
            consultation_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            justifying_quote=f"« {quote} »",
            uc3_entity=entity,
            quality=quality,
            publicity="publique" if is_public else "interne",
            confidence=confidence,
            gap_or_alert=gap_alert_str,
            proposed_action=action,
            status_category=status_category,
            the_points=eval_result.get("total_points", 0.0),
            the_max_points=eval_result.get("max_possible_points", 3.0),
            the_percentage=eval_result.get("score_percentage", 0.0),
            is_self_contained=eval_result.get("is_self_contained", True),
            is_link_farm_rejected=is_link_farm
        )
