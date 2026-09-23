"""
Référentiel Méthodologique Officiel - THE Sustainability Impact Ratings 2027 (Version 1.0)
Université Constantine 3 (UC3) Salah Boubnider
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

TAXONOMY_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "the_2027_taxonomy.json"

class THE2027Framework:
    def __init__(self, taxonomy_path: Optional[Path] = None):
        self.taxonomy_path = taxonomy_path or TAXONOMY_PATH
        with open(self.taxonomy_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.sdgs = self.data.get("sdgs", {})
        self.scoring_rules = self.data.get("scoring_rules", {})
        self.target_year = self.scoring_rules.get("target_academic_year", 2025)

    def get_sdg(self, sdg_num: int | str) -> Optional[Dict[str, Any]]:
        return self.sdgs.get(str(sdg_num))

    def get_all_sdgs(self) -> Dict[str, Dict[str, Any]]:
        return self.sdgs

    def get_indicator(self, indicator_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve indicator details by ID e.g. '17.2.1' or '1.3.1'."""
        parts = indicator_id.split(".")
        if len(parts) < 2:
            return None
        sdg_id = parts[0]
        metric_id = f"{parts[0]}.{parts[1]}"
        sdg = self.get_sdg(sdg_id)
        if not sdg:
            return None
        metric = sdg.get("metrics", {}).get(metric_id)
        if not metric:
            return None
        indicator = metric.get("indicators", {}).get(indicator_id)
        if indicator:
            # enrich with metric & sdg context
            res = dict(indicator)
            res["indicator_id"] = indicator_id
            res["metric_name"] = metric.get("name")
            res["sdg_number"] = int(sdg_id)
            res["sdg_name"] = sdg.get("name")
            return res
        return None

    def get_indicators_for_sdg(self, sdg_num: int | str) -> List[Dict[str, Any]]:
        sdg = self.get_sdg(sdg_num)
        if not sdg:
            return []
        indicators = []
        for metric_id, metric in sdg.get("metrics", {}).items():
            for ind_id, ind_data in metric.get("indicators", {}).items():
                item = dict(ind_data)
                item["indicator_id"] = ind_id
                item["metric_id"] = metric_id
                item["metric_name"] = metric.get("name")
                item["sdg_number"] = int(sdg_num)
                item["sdg_name"] = sdg.get("name")
                indicators.append(item)
        return indicators

    def evaluate_score(
        self,
        indicator_id: str,
        statement_exists: bool,
        evidence_quality: str,  # 'specific', 'general', 'not_relevant', 'none'
        is_public: bool,
        policy_reviewed_2022_2026: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate score based on THE 2027 rules:
        - Statement: up to 1 point
        - Evidence: 1.0 (Specific), 0.5 (General), 0.0 (Not relevant)
        - Public: 1.0 (Public web URL), 0.0 (Internal/Attached document)
        - Policy review bonus: 1.0 (if created or reviewed between 2022 and 2026 for eligible policies)
        """
        ind = self.get_indicator(indicator_id)
        max_pts = ind.get("max_points", 3) if ind else 3
        has_bonus = ind.get("reviewed_policy_bonus", False) if ind else False

        statement_pts = 1.0 if statement_exists else 0.0
        
        quality_map = {
            "specific": 1.0,
            "general": 0.5,
            "not_relevant": 0.0,
            "none": 0.0
        }
        evidence_pts = quality_map.get(evidence_quality.lower(), 0.0)
        
        # In THE methodology, evidence points only apply if evidence is actually provided
        public_pts = 1.0 if (is_public and evidence_pts > 0) else 0.0
        review_pts = 1.0 if (has_bonus and policy_reviewed_2022_2026 and statement_exists) else 0.0

        total_pts = statement_pts + evidence_pts + public_pts + review_pts
        # Cap to max points
        total_pts = min(total_pts, float(max_pts))

        percentage_achieved = (total_pts / max_pts) * 100.0 if max_pts > 0 else 0.0
        
        return {
            "indicator_id": indicator_id,
            "statement_points": statement_pts,
            "evidence_points": evidence_pts,
            "public_points": public_pts,
            "policy_review_points": review_pts,
            "total_points": total_pts,
            "max_points": max_pts,
            "percentage_achieved": round(percentage_achieved, 2)
        }

    def compute_overall_rank_score(self, sdg_scaled_scores: Dict[int, float]) -> Dict[str, Any]:
        """
        Calculates THE Overall Impact Rating Score:
        - SDG 17 is MANDATORY and accounts for 22% of the overall score.
        - The top 3 other SDGs each account for 26% (3 x 26% = 78%).
        Total = 22% + 78% = 100%.
        """
        sdg17_score = sdg_scaled_scores.get(17, 0.0)
        
        other_scores = [
            (sdg_num, score) for sdg_num, score in sdg_scaled_scores.items() if sdg_num != 17
        ]
        # Sort descending
        other_scores.sort(key=lambda x: x[1], reverse=True)
        top_3 = other_scores[:3]
        
        top_3_sum = sum(score for _, score in top_3)
        overall_score = (sdg17_score * 0.22) + sum(score * 0.26 for _, score in top_3)
        
        return {
            "sdg_17_score": sdg17_score,
            "top_3_sdgs": top_3,
            "overall_score": round(overall_score, 2),
            "is_eligible_overall": (len(other_scores) >= 3 and 17 in sdg_scaled_scores)
        }
