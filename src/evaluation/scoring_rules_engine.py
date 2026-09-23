"""
Moteur de Règles Déterministe - THE Sustainability Impact Ratings 2027
Université Constantine 3 (UC3) Salah Boubnider

Règle d'or : Le LLM extrait UNIQUEMENT les faits observés.
Le calcul des points est 100% déterministe, arithmétique et auditable.
"""

from typing import Dict, Any, List, Optional


class IndicatorScoringRulesEngine:
    """Moteur arithmétique de calcul conforme aux sous-barèmes officiels THE 2027."""

    def __init__(self):
        pass

    def calculate_score(
        self,
        indicator_id: str,
        facts: Dict[str, Any],
        source_verified: bool = False,
        source_is_attachment: bool = False,
        is_policy_bonus_eligible: bool = False,
        methodology_question: str = ""
    ) -> Dict[str, Any]:
        """
        Calcule les points officiels de façon déterministe à partir des faits extraits.
        """
        # 1. Validation de l'autosuffisance et de la pertinence
        quality = facts.get("quality", "not_relevant")
        is_self_contained = facts.get("is_self_contained", True) is not False
        is_link_farm = facts.get("is_link_farm", False) is True

        is_relevant = (quality in ("specific", "general")) and is_self_contained and not is_link_farm

        # Caractère public : uniquement page crawlée avec succès (HTTP 200)
        is_public = bool(source_verified and not source_is_attachment)

        # 2. Aiguillage selon l'indicateur spécifique
        if indicator_id == "13.4.1":
            return self._calculate_13_4_1(facts, is_relevant, quality, is_public)
        elif indicator_id == "13.4.2":
            return self._calculate_13_4_2(facts, is_relevant, quality, is_public)
        elif indicator_id == "13.2.1":
            return self._calculate_13_2_1(facts, is_relevant, quality, is_public)
        else:
            return self._calculate_standard_or_policy(
                indicator_id, facts, is_relevant, quality, is_public,
                is_policy_bonus_eligible, methodology_question
            )

    def _calculate_13_4_1(
        self,
        facts: Dict[str, Any],
        is_relevant: bool,
        quality: str,
        is_public: bool
    ) -> Dict[str, Any]:
        """
        13.4.1 Commitment to carbon neutral university (Maximum 5 points)
        - Existence of target: 1.0 pt
        - Evidence provided: 1.0 pt (spécifique) / 0.5 pt (générale)
        - Is evidence public: 1.0 pt
        - Scopes covered: jusqu'à 3 pts (Scope 1: 0, Scopes 1-2: 1.0, Scopes 1-3 partiel: 2.0, Scopes 1-3 full: 3.0)
        """
        max_pts = 5.0

        if not is_relevant:
            return self._build_result(
                indicator_id="13.4.1",
                max_points=max_pts,
                total_earned=0.0,
                is_relevant=False,
                quality=quality,
                is_public=is_public,
                components=[
                    {"id": "existence", "name": "Existence of target", "maximum": 1.0, "earned": 0.0},
                    {"id": "evidence_relevance", "name": "Evidence provided", "maximum": 1.0, "earned": 0.0},
                    {"id": "public_visibility", "name": "Public access", "maximum": 1.0, "earned": 0.0},
                    {"id": "scopes_covered", "name": "GHG Scopes covered (1-3)", "maximum": 3.0, "earned": 0.0}
                ]
            )

        # Existence of target is a mandatory prerequisite
        c_existence_ok = bool(facts.get("is_target_or_action_declared", True))
        if not c_existence_ok:
            return self._build_result(
                indicator_id="13.4.1",
                max_points=max_pts,
                total_earned=0.0,
                is_relevant=True,
                quality=quality,
                is_public=is_public,
                components=[
                    {"id": "existence", "name": "Existence of target (prerequisite)", "maximum": 0.0, "earned": 0.0},
                    {"id": "evidence_relevance", "name": "Evidence provided", "maximum": 1.0, "earned": 0.0},
                    {"id": "public_visibility", "name": "Public access", "maximum": 1.0, "earned": 0.0},
                    {"id": "scopes_covered", "name": "GHG Scopes covered (1-3)", "maximum": 3.0, "earned": 0.0}
                ]
            )

        # Preuve (jusqu'à 1 point)
        c_evidence = 1.0 if quality == "specific" else 0.5
        # Public (1 point si public et preuve pertinente)
        c_public = 1.0 if is_public else 0.0
        # Scopes GHG (jusqu'à 3 points : 0 / 1 / 2 / 3)
        scope_str = str(facts.get("scopes_identified", "")).lower()
        if "full" in scope_str or "1_2_3_full" in scope_str:
            c_scopes = 3.0
        elif "partial" in scope_str or "1_2_3_partial" in scope_str or "scope 3" in scope_str or "scope3" in scope_str:
            c_scopes = 2.0
        elif "scope 2" in scope_str or "scope2" in scope_str or "scopes_1_2" in scope_str:
            c_scopes = 1.0
        else:
            c_scopes = 0.0

        total = min(c_evidence + c_public + c_scopes, max_pts)

        return self._build_result(
            indicator_id="13.4.1",
            max_points=max_pts,
            total_earned=total,
            is_relevant=True,
            quality=quality,
            is_public=is_public,
            components=[
                {"id": "existence", "name": "Existence of target (prerequisite)", "maximum": 0.0, "earned": 0.0},
                {"id": "evidence_relevance", "name": "Evidence provided", "maximum": 1.0, "earned": c_evidence},
                {"id": "public_visibility", "name": "Public access", "maximum": 1.0, "earned": c_public},
                {"id": "scopes_covered", "name": "GHG Scopes covered (1-3)", "maximum": 3.0, "earned": c_scopes}
            ]
        )

    def _calculate_13_4_2(
        self,
        facts: Dict[str, Any],
        is_relevant: bool,
        quality: str,
        is_public: bool
    ) -> Dict[str, Any]:
        """
        13.4.2 Achieve by date (Maximum 4 points)
        - Prior to 2025: 4.0 points
        - 2025-2029: 3.0 points
        - 2030-2039: 2.0 points
        - 2040-2049: 1.0 point
        - 2050 or later: 0.5 point
        """
        max_pts = 4.0

        if not is_relevant:
            return self._build_result(
                indicator_id="13.4.2",
                max_points=max_pts,
                total_earned=0.0,
                is_relevant=False,
                quality=quality,
                is_public=is_public,
                components=[
                    {"id": "achieve_date_bracket", "name": "Target achievement date bracket", "maximum": 4.0, "earned": 0.0}
                ]
            )

        bracket = str(facts.get("achieve_date_bracket", "")).lower()
        target_yr = facts.get("detected_year")

        earned = 0.0
        if "prior" in bracket or (isinstance(target_yr, int) and target_yr < 2025):
            earned = 4.0
        elif "2025_2029" in bracket or (isinstance(target_yr, int) and 2025 <= target_yr <= 2029):
            earned = 3.0
        elif "2030_2039" in bracket or (isinstance(target_yr, int) and 2030 <= target_yr <= 2039):
            earned = 2.0
        elif "2040_2049" in bracket or (isinstance(target_yr, int) and 2040 <= target_yr <= 2049):
            earned = 1.0
        elif "2050" in bracket or (isinstance(target_yr, int) and target_yr >= 2050):
            earned = 0.5
        else:
            earned = 0.5 if quality == "specific" else 0.0

        return self._build_result(
            indicator_id="13.4.2",
            max_points=max_pts,
            total_earned=earned,
            is_relevant=True,
            quality=quality,
            is_public=is_public,
            components=[
                {"id": "achieve_date_bracket", "name": "Target achievement date bracket", "maximum": 4.0, "earned": earned}
            ]
        )

    def _calculate_13_2_1(
        self,
        facts: Dict[str, Any],
        is_relevant: bool,
        quality: str,
        is_public: bool
    ) -> Dict[str, Any]:
        """
        13.2.1 Low carbon energy tracking (Maximum 3 points)
        - Existence of measurement: 1.0 for whole university, 0.5 for partial measurement
        - Evidence provided: up to 1.0 pt
        - Public access: 1.0 pt
        """
        max_pts = 3.0

        if not is_relevant:
            return self._build_result(
                indicator_id="13.2.1",
                max_points=max_pts,
                total_earned=0.0,
                is_relevant=False,
                quality=quality,
                is_public=is_public,
                components=[
                    {"id": "existence", "name": "Measurement scope (whole vs partial)", "maximum": 1.0, "earned": 0.0},
                    {"id": "evidence_relevance", "name": "Evidence provided", "maximum": 1.0, "earned": 0.0},
                    {"id": "public_visibility", "name": "Public access", "maximum": 1.0, "earned": 0.0}
                ]
            )

        scope = str(facts.get("measurement_scope", "whole_university")).lower()
        c_exist = 1.0 if ("whole" in scope or "complete" in scope) else 0.5
        c_evidence = 1.0 if quality == "specific" else 0.5
        c_public = 1.0 if is_public else 0.0

        total = min(c_exist + c_evidence + c_public, max_pts)

        return self._build_result(
            indicator_id="13.2.1",
            max_points=max_pts,
            total_earned=total,
            is_relevant=True,
            quality=quality,
            is_public=is_public,
            components=[
                {"id": "existence", "name": "Measurement scope (whole vs partial)", "maximum": 1.0, "earned": c_exist},
                {"id": "evidence_relevance", "name": "Evidence provided", "maximum": 1.0, "earned": c_evidence},
                {"id": "public_visibility", "name": "Public access", "maximum": 1.0, "earned": c_public}
            ]
        )

    def _calculate_standard_or_policy(
        self,
        indicator_id: str,
        facts: Dict[str, Any],
        is_relevant: bool,
        quality: str,
        is_public: bool,
        is_policy_bonus_eligible: bool,
        methodology_question: str
    ) -> Dict[str, Any]:
        """
        Calcul standard qualitatif (3 points) ou politique révisée (4 points).
        """
        has_policy_bonus = is_policy_bonus_eligible or (
            "2022-2026" in methodology_question and ("four points" in methodology_question.lower() or "created or reviewed" in methodology_question.lower())
        )
        max_pts = 4.0 if has_policy_bonus else 3.0

        if not is_relevant:
            components = [
                {"id": "existence", "name": "Déclaration / Action", "maximum": 1.0, "earned": 0.0},
                {"id": "evidence_relevance", "name": "Pertinence de la preuve", "maximum": 1.0, "earned": 0.0},
                {"id": "public_visibility", "name": "Caractère public", "maximum": 1.0, "earned": 0.0}
            ]
            if has_policy_bonus:
                components.append({"id": "policy_bonus", "name": "Bonus révision 2022-2026", "maximum": 1.0, "earned": 0.0})

            return self._build_result(
                indicator_id=indicator_id,
                max_points=max_pts,
                total_earned=0.0,
                is_relevant=False,
                quality=quality,
                is_public=is_public,
                components=components
            )

        c_declaration = 1.0 if facts.get("is_target_or_action_declared", True) else 0.0
        c_evidence = 1.0 if quality == "specific" else 0.5
        c_public = 1.0 if is_public else 0.0

        c_bonus = 0.0
        if has_policy_bonus:
            rev_yr = facts.get("policy_revision_year") or facts.get("detected_year")
            is_rev = facts.get("policy_reviewed_2022_2026") is True or (isinstance(rev_yr, int) and 2022 <= rev_yr <= 2026)
            if is_rev:
                c_bonus = 1.0

        total = min(c_declaration + c_evidence + c_public + c_bonus, max_pts)

        components = [
            {"id": "existence", "name": "Déclaration / Action", "maximum": 1.0, "earned": c_declaration},
            {"id": "evidence_relevance", "name": "Pertinence de la preuve", "maximum": 1.0, "earned": c_evidence},
            {"id": "public_visibility", "name": "Caractère public", "maximum": 1.0, "earned": c_public}
        ]
        if has_policy_bonus:
            components.append({"id": "policy_bonus", "name": "Bonus révision 2022-2026", "maximum": 1.0, "earned": c_bonus})

        return self._build_result(
            indicator_id=indicator_id,
            max_points=max_pts,
            total_earned=total,
            is_relevant=True,
            quality=quality,
            is_public=is_public,
            components=components
        )

    def _build_result(
        self,
        indicator_id: str,
        max_points: float,
        total_earned: float,
        is_relevant: bool,
        quality: str,
        is_public: bool,
        components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Structure le résultat normalisé conforme aux audits THE."""
        percentage = round(100.0 * total_earned / max_points, 1) if max_points > 0 else 0.0

        # Mapping des composantes pour rétro-compatibilité
        statement_pts = 0.0
        evidence_pts = 0.0
        public_pts = 0.0
        policy_pts = 0.0

        for comp in components:
            cid = comp["id"]
            if cid in ("existence", "achieve_date_bracket"):
                statement_pts = comp["earned"]
            elif cid == "evidence_relevance":
                evidence_pts = comp["earned"]
            elif cid == "public_visibility":
                public_pts = comp["earned"]
            elif cid in ("policy_bonus", "scopes_covered"):
                policy_pts = comp["earned"]

        if not is_relevant:
            status_cat = "Absence de donnée"
            action = "rejeter"
        else:
            status_cat = "Information vérifiée" if (is_public and evidence_pts >= 1.0) else "Information à confirmer"
            action = "valider" if (is_public and evidence_pts >= 1.0) else "publier"

        return {
            "indicator_id": indicator_id,
            "the_points_earned": total_earned,
            "the_max_points": max_points,
            "the_percentage": percentage,
            "is_relevant": is_relevant,
            "quality": quality if is_relevant else "not_relevant",
            "is_public": is_public,
            "components": components,
            "statement_points": statement_pts,
            "evidence_points": evidence_pts,
            "public_points": public_pts,
            "policy_bonus_points": policy_pts,
            "status_category": status_cat,
            "proposed_action": action
        }
