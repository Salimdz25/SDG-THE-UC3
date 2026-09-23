"""
Modèles de Données Structurées pour les Fiches d'Indicateurs UC3
Conforme aux 5 fonctions et à la fiche structurée requise par l'Université Constantine 3
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class IndicatorFiche:
    odd_indicator: str                         # Ex: "17.2.4"
    indicator_title: str                       # Titre de l'indicateur
    methodological_requirement: str            # Ce que l'indicateur demande exactement selon THE 2027
    information_found: str                     # Fait ou valeur extraite
    year: Optional[int] = None                 # Année (Priorité 2025)
    source_exact: str = ""                     # URL ou document d'origine
    consultation_date: str = ""                # Date de consultation de la source
    justifying_quote: str = ""                 # Passage directement vérifiable (citation verbatim)
    uc3_entity: str = ""                       # Rectorat, Faculté, Laboratoire, Service...
    quality: str = "non_pertinente"            # "spécifique", "générale", "non_pertinente"
    publicity: str = "interne"                 # "publique" ou "interne"
    confidence: str = "faible"                 # "élevée", "moyenne", "faible"
    gap_or_alert: str = ""                     # Information manquante, risque ou contradiction
    proposed_action: str = "vérifier"          # "publier", "compléter", "vérifier", "rejeter"
    
    # Règle d'or : Catégorie d'affirmation
    # Valeurs permises : "Information vérifiée", "Inférence", "Information à confirmer", "Absence de donnée"
    status_category: str = "Absence de donnée"
    
    # Calcul THE
    the_points: float = 0.0
    the_max_points: float = 3.0
    the_percentage: float = 0.0
    is_self_contained: bool = True
    is_link_farm_rejected: bool = False
    
    # Workflow de validation humaine
    human_validation_status: str = "En attente de validation"  # "Validé", "Rejeté", "Modifié"
    validation_comment: str = ""
    assigned_responsible: str = "Comité ODD UC3"
    due_date: str = "2026-11-30"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
