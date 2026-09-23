"""Tests for deterministic scoring rules engine (THE 2027)."""

import pytest
from src.evaluation.scoring_rules_engine import IndicatorScoringRulesEngine


@pytest.fixture
def engine():
    return IndicatorScoringRulesEngine()


def test_13_4_1_full_scopes_yields_5_points(engine):
    facts = {
        "is_target_or_action_declared": True,
        "quality": "specific",
        "is_self_contained": True,
        "is_link_farm": False,
        "scopes_identified": "scopes_1_2_3_full",
    }
    res = engine.calculate_score("13.4.1", facts, source_verified=True, source_is_attachment=False)
    assert res["the_max_points"] == 5.0
    assert res["the_points_earned"] == 5.0
    assert res["the_percentage"] == 100.0
    assert len(res["components"]) == 4

    comp_dict = {c["id"]: c["earned"] for c in res["components"]}
    assert comp_dict["existence"] == 0.0
    assert comp_dict["evidence_relevance"] == 1.0
    assert comp_dict["public_visibility"] == 1.0
    assert comp_dict["scopes_covered"] == 3.0


def test_13_4_1_partial_scopes_yields_4_points(engine):
    facts = {
        "is_target_or_action_declared": True,
        "quality": "specific",
        "is_self_contained": True,
        "is_link_farm": False,
        "scopes_identified": "scopes_1_2_3_partial",
    }
    res = engine.calculate_score("13.4.1", facts, source_verified=True, source_is_attachment=False)
    assert res["the_points_earned"] == 4.0
    comp_dict = {c["id"]: c["earned"] for c in res["components"]}
    assert comp_dict["scopes_covered"] == 2.0


def test_13_4_1_irrelevant_evidence_strictly_zero(engine):
    facts = {
        "is_target_or_action_declared": True,
        "quality": "not_relevant",
        "is_self_contained": True,
        "is_link_farm": False,
        "scopes_identified": "scopes_1_2_3_full",
    }
    res = engine.calculate_score("13.4.1", facts, source_verified=True, source_is_attachment=False)
    assert res["the_points_earned"] == 0.0
    assert res["the_percentage"] == 0.0
    assert res["status_category"] == "Absence de donnée"


def test_13_4_2_date_brackets(engine):
    # Bracket prior to 2025 -> 4.0 points
    res_prior = engine.calculate_score(
        "13.4.2",
        {"quality": "specific", "is_self_contained": True, "achieve_date_bracket": "prior_2025"},
        source_verified=True
    )
    assert res_prior["the_points_earned"] == 4.0
    assert res_prior["the_max_points"] == 4.0

    # Bracket 2025-2029 -> 3.0 points
    res_2027 = engine.calculate_score(
        "13.4.2",
        {"quality": "specific", "is_self_contained": True, "detected_year": 2027},
        source_verified=True
    )
    assert res_2027["the_points_earned"] == 3.0

    # Bracket 2050 -> 0.5 point
    res_2050 = engine.calculate_score(
        "13.4.2",
        {"quality": "specific", "is_self_contained": True, "detected_year": 2050},
        source_verified=True
    )
    assert res_2050["the_points_earned"] == 0.5


def test_13_2_1_whole_vs_partial(engine):
    # Whole university
    res_whole = engine.calculate_score(
        "13.2.1",
        {"quality": "specific", "is_self_contained": True, "measurement_scope": "whole_university"},
        source_verified=True
    )
    assert res_whole["the_points_earned"] == 3.0  # 1.0 (whole) + 1.0 (ev) + 1.0 (pub)

    # Partial measurement
    res_partial = engine.calculate_score(
        "13.2.1",
        {"quality": "specific", "is_self_contained": True, "measurement_scope": "partial"},
        source_verified=True
    )
    assert res_partial["the_points_earned"] == 2.5  # 0.5 (partial) + 1.0 (ev) + 1.0 (pub)


def test_standard_and_policy_indicators(engine):
    # Standard 3 points
    res_std = engine.calculate_score(
        "1.3.1",
        {"quality": "specific", "is_self_contained": True},
        source_verified=True
    )
    assert res_std["the_max_points"] == 3.0
    assert res_std["the_points_earned"] == 3.0

    # Policy with 2022-2026 revision -> 4.0 points
    res_pol = engine.calculate_score(
        "12.2.1",
        {"quality": "specific", "is_self_contained": True, "policy_reviewed_2022_2026": True},
        source_verified=True,
        is_policy_bonus_eligible=True
    )
    assert res_pol["the_max_points"] == 4.0
    assert res_pol["the_points_earned"] == 4.0
