"""
Simulateur de Validation THE LLM - Impact Ratings 2027
Vérifie la conformité des preuves aux exigences strictes de Times Higher Education :
- Autosuffisance du contenu (Interdiction de renvoi vers d'autres liens)
- Détection des catalogues/répertoires de liens (Rejet éliminatoire)
- Évaluation de la pertinence (Spécifique 1.0, Générale 0.5, Non-pertinente 0.0)
- Statut de publicité (URL publique directe vs Document attaché noté 0)
- Vérification temporelle (Année 2025 / Politiques 2022-2026)
"""

import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

class THEEvidenceEvaluator:
    def __init__(self, target_year: int = 2025):
        self.target_year = target_year

    def audit_evidence(
        self,
        indicator_id: str,
        indicator_definition: str,
        evidence_text: str,
        source_url_or_path: str,
        declared_year: Optional[int] = None,
        is_policy_indicator: bool = False
    ) -> Dict[str, Any]:
        """
        Analyse une preuve et simule le modèle de validation IA de THE.
        Retourne l'évaluation, les points, les alertes de non-conformité et les recommandations.
        """
        alerts = []
        recommendations = []
        is_public = False
        is_link_farm = False
        quality = "not_relevant"
        
        # 1. Vérification du caractère public (URL vs Fichier local/interne)
        parsed = urlparse(source_url_or_path)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            is_public = True
        else:
            is_public = False
            alerts.append(
                "ATTENTION : Preuve issue d'un fichier local ou interne. Selon la méthodologie THE 2027 (page 9), "
                "tout document soumis sous forme de pièce jointe est automatiquement noté 'Non public' (0 point)."
            )
            recommendations.append(
                "Héberger et publier ce document directement sur le site officiel de l'UC3 (ex: univ-constantine3.dz/odd/...) "
                "pour obtenir le point complet de publicité (1.0 pt)."
            )

        # 2. Détection des pages Facebook
        if "facebook.com" in source_url_or_path.lower():
            alerts.append(
                "NOTE FACEBOOK : Les publications Facebook peuvent être éphémères ou nécessiter une connexion. "
                "THE exige une preuve directement visible et pérenne."
            )
            recommendations.append(
                "Transformer le compte-rendu Facebook en article institutionnel permanent sur le portail web de l'UC3 "
                "avec date, photos et procès-verbal d'activité."
            )

        # 3. Contrôle d'autosuffisance et détection des répertoires de liens (Règle d'exclusion THE 2027)
        url_matches = re.findall(r"https?://[^\s]+", evidence_text or "")
        word_count = len((evidence_text or "").split())
        
        # Si le texte contient beaucoup de liens et peu de contenu explicatif, c'est un répertoire de liens
        if len(url_matches) >= 3 and (word_count / max(len(url_matches), 1)) < 15:
            is_link_farm = True
            alerts.append(
                "REJET ÉLIMINATOIRE THE : La preuve ressemble à un annuaire de liens. "
                "La méthodologie THE 2027 stipule que les fichiers contenant de multiples liens sont désormais rejetés."
            )
            recommendations.append(
                "Fournir un exemple direct avec le texte complet et chiffré décrivant l'action sans renvoyer vers des liens secondaires."
            )
            quality = "not_relevant"

        # 4. Contrôle de l'année cible (2025)
        detected_years = [int(y) for y in re.findall(r"\b(20[12][0-9])\b", evidence_text or "")]
        effective_year = declared_year or (detected_years[0] if detected_years else None)

        if is_policy_indicator:
            # Pour les politiques, révisées entre 2022 et 2026 est valorisé
            policy_reviewed_valid = False
            if effective_year and 2022 <= effective_year <= 2026:
                policy_reviewed_valid = True
            elif not effective_year:
                alerts.append("Politique sans date de révision mentionnée. Spécifier la date (2022-2026 requis pour le bonus).")
        else:
            policy_reviewed_valid = False
            if effective_year and effective_year != self.target_year:
                alerts.append(
                    f"ANOMALIE DATE : La donnée identifiée mentionne l'année {effective_year}. "
                    f"Le référentiel THE 2027 exige impérativement des données de l'année {self.target_year}."
                )
                recommendations.append(f"Mettre à jour l'indicateur avec les données consolidées de l'année {self.target_year}.")

        # 5. Évaluation de la qualité de la preuve (si non rejetée comme link farm)
        if not is_link_farm:
            text_lower = (evidence_text or "").lower()
            def_lower = f"{indicator_definition} {indicator_id}".lower()
            
            # Dictionnaire sémantique thématique étendu
            thematic_keywords_map = {
                "poverty": ["pauvreté", "poverty", "faible revenu", "low income", "bourse", "bourses", "aide financière", "financial aid", "quintile", "فقر", "منحة"],
                "hunger": ["faim", "hunger", "alimentation", "food", "déchets alimentaires", "food waste", "agronomie", "agriculture", "aquaculture", "تغذية", "أمن غذائي"],
                "health": ["santé", "health", "médical", "médecine", "clinique", "bien-être", "well-being", "fumée", "tabac", "smoke-free", "صحة", "طب"],
                "education": ["éducation", "education", "enseignement", "pédagogie", "formation continue", "lifelong learning", "premier cycle", "diplôme", "تعليم"],
                "gender": ["genre", "femme", "femmes", "women", "gender", "maternité", "maternity", "discrimination", "égalité", "parité", "مرأة", "نوع اجتماعي"],
                "water": ["eau", "water", "assainissement", "sanitation", "eaux usées", "wastewater", "recyclage de l'eau", "pluie", "aquifère", "مياه", "صرف صحي"],
                "energy": ["énergie", "energy", "renouvelable", "renewable", "solaire", "solar", "efficacité énergétique", "carbone", "carbon", "طاقة", "طاقة متجددة"],
                "work": ["travail", "work", "emploi", "salaires", "living wage", "syndicat", "union", "stage", "placement", "عمل", "توظيف"],
                "industry": ["industrie", "industry", "innovation", "brevet", "patents", "spin-off", "start-up", "infrastructure", "صناعة", "ابتكار"],
                "inequality": ["inégalité", "inequality", "handicap", "disability", "inclusion", "diversité", "minorité", "مساواة", "إعاقة"],
                "cities": ["ville", "cities", "communauté", "patrimoine", "heritage", "transport", "logement", "housing", "musée", "espace vert", "تراث", "مدن"],
                "consumption": ["consommation", "consumption", "déchets", "waste", "recyclage", "plastique", "plastic", "approvisionnement", "sourcing", "استهلاك", "تدوير"],
                "climate": ["climat", "climate", "neutralité carbone", "carbon neutral", "catastrophe", "disaster", "ges", "ghg", "مناخ", "تغير مناخي"],
                "water_life": ["océan", "mer", "marins", "marine", "aquatique", "pêche", "fisheries", "cours d'eau", "بحار", "أحياء مائية"],
                "land_life": ["biodiversité", "biodiversity", "forêt", "forest", "écosystème", "ecosystem", "espèces", "faune", "flore", "terrestre", "تنوع بيولوجي"],
                "peace": ["paix", "peace", "justice", "droit", "law", "gouvernance", "transparence", "corruption", "liberté académique", "عدالة", "قانون"],
                "partnerships": ["partenariat", "partnership", "collaboration", "coopération", "dialogue", "ong", "ngo", "gouvernement", "government", "intersectoriel", "rapport odd", "sdg report", "convention", "شراكة", "تعاون"]
            }

            # Trouver les thématiques concernées par cet indicateur
            active_themes = set()
            for theme, kw_list in thematic_keywords_map.items():
                if any(kw in def_lower for kw in kw_list):
                    active_themes.add(theme)

            # Vérifier si la preuve traite RÉELLEMENT d'au moins un thème clé de l'indicateur
            matched_themes = set()
            for theme in active_themes:
                kw_list = thematic_keywords_map[theme]
                if any(kw in text_lower for kw in kw_list):
                    matched_themes.add(theme)

            # Mots spécifiques de l'intitulé (excluant mots vides)
            stop_words = {"this", "that", "with", "from", "about", "your", "have", "been", "year", "which", "across",
                          "dans", "pour", "avec", "cette", "sont", "leur", "plus", "tous", "tout", "vers", "afin"}
            def_words = {w for w in re.findall(r"\b[a-zA-Z\u0600-\u06FF]{4,}\b", def_lower) if w not in stop_words}
            direct_overlap = [w for w in def_words if w in text_lower]

            has_numeric_data = bool(re.search(r"\b\d+([.,]\d+)?\b", evidence_text or ""))
            has_institutional_entity = any(kw in text_lower for kw in [
                "université", "constantine", "faculté", "laboratoire", "rectorat", "معهد", "جامعة", "قسنطينة", "uc3"
            ])

            # RÈGLE STRICTE : Si AUCUN thème de l'indicateur ni mot-clé significatif n'est présent -> NON PERTINENT
            is_thematically_relevant = (len(matched_themes) > 0) or (len(direct_overlap) >= 2)

            if not is_thematically_relevant:
                quality = "not_relevant"
                alerts.append(
                    "PREUVE NON PERTINENTE (HORS-SUJET) : Le texte soumis ne traite pas de la thématique "
                    f"spécifique requise par cet indicateur ({indicator_id}). La simple mention de l'université ne suffit pas."
                )
                recommendations.append("Soumettre un document ou un lien qui porte explicitement sur les exigences de cet indicateur.")
            else:
                # Évaluer la précision (Spécifique vs Générale)
                if (len(matched_themes) >= 2 or len(direct_overlap) >= 3) and (has_numeric_data or len(text_lower) > 90):
                    quality = "specific"
                elif len(matched_themes) >= 1 or len(direct_overlap) >= 1:
                    quality = "general"
                    recommendations.append(
                        "Preuve générale : pour obtenir la note maximale 'Spécifique' (1,0 pt), ajoutez des données "
                        "quantitatives, des dates précises et les résultats concrets de l'action."
                    )
                else:
                    quality = "not_relevant"

        # Calcul des scores : si non pertinent -> STRICTEMENT 0 POINT
        if quality == "not_relevant":
            statement_points = 0.0
            evidence_points = 0.0
            public_points = 0.0
            policy_bonus_points = 0.0
            total_points = 0.0
        else:
            points_map = {"specific": 1.0, "general": 0.5, "not_relevant": 0.0}
            evidence_points = points_map.get(quality, 0.0)
            statement_points = 1.0
            public_points = 1.0 if (is_public and evidence_points > 0) else 0.0
            policy_bonus_points = 1.0 if (is_policy_indicator and policy_reviewed_valid and statement_points > 0) else 0.0
            total_points = statement_points + evidence_points + public_points + policy_bonus_points

        total_points = statement_points + evidence_points + public_points + policy_bonus_points
        max_possible = 4.0 if is_policy_indicator else 3.0

        return {
            "indicator_id": indicator_id,
            "quality": quality,
            "is_public": is_public,
            "is_link_farm": is_link_farm,
            "detected_year": effective_year,
            "statement_points": statement_points,
            "evidence_points": evidence_points,
            "public_points": public_points,
            "policy_bonus_points": policy_bonus_points,
            "total_points": total_points,
            "max_possible_points": max_possible,
            "score_percentage": round((total_points / max_possible) * 100, 1),
            "alerts": alerts,
            "recommendations": recommendations,
            "is_self_contained": not is_link_farm and len((evidence_text or "").strip()) > 30
        }
