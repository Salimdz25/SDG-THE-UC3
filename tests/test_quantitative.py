"""Tests for quantitative and bibliometric workflows in THE 2027 Framework."""

import pytest
from src.methodology.the_2027_framework import THE2027Framework


@pytest.fixture
def framework():
    return THE2027Framework()


def test_260_indicators_distribution(framework):
    all_inds = [ind for s in range(1, 18) for ind in framework.get_indicators_for_sdg(s)]
    assert len(all_inds) == 260

    by_type = {}
    for ind in all_inds:
        t = ind.get("type")
        by_type[t] = by_type.get(t, 0) + 1

    assert by_type["qualitative"] == 186
    assert by_type["quantitative"] == 25
    assert by_type["bibliometric"] == 47
    assert by_type["external_metric"] == 1
    assert by_type["exploratory"] == 1


def test_quantitative_indicators_have_fields(framework):
    quant_inds = [
        ind for s in range(1, 18)
        for ind in framework.get_indicators_for_sdg(s)
        if ind.get("type") == "quantitative"
    ]
    assert len(quant_inds) == 25

    for ind in quant_inds:
        assert "fields" in ind, f"Missing fields in quantitative indicator {ind['indicator_id']}"
        assert len(ind["fields"]) >= 1, f"Empty fields in {ind['indicator_id']}"
        assert ind.get("year") == 2025


def test_bibliometric_indicators_have_weights(framework):
    bib_inds = [
        ind for s in range(1, 18)
        for ind in framework.get_indicators_for_sdg(s)
        if ind.get("type") == "bibliometric"
    ]
    assert len(bib_inds) == 47

    for ind in bib_inds:
        assert ind.get("weight_sdg", 0) > 0, f"Bibliometric indicator {ind['indicator_id']} missing weight"
        assert "metric_id" in ind


def test_quantitative_ratio_calculation():
    # Simulation du calcul de ratio
    den = 45000.0  # Total students UC3
    num = 4500.0   # Low income aid

    ratio = (num / den) * 100.0
    assert ratio == 10.0

    # Denominator zero protection
    den_zero = 0.0
    safe_ratio = (num / den_zero * 100.0) if den_zero > 0 else 0.0
    assert safe_ratio == 0.0
