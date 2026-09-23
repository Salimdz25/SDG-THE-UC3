"""Unit tests for Indicator Type filtering and Bibliometric rules in THE 2027 Dashboard."""

import pytest
from src.methodology.the_2027_framework import (
    THE2027Framework,
    FILTER_PROOF,
    FILTER_NUMERIC,
    FILTER_BIBLIO,
    FILTER_ALL,
)


@pytest.fixture
def framework():
    return THE2027Framework()


def test_filters_total_counts_across_all_sdgs(framework):
    """Verify indicator distribution across the 4 filter options for all 17 SDGs."""
    all_inds = [ind for s in range(1, 18) for ind in framework.get_indicators_for_sdg(s)]
    assert len(all_inds) == 260

    proof_inds = framework.filter_indicators(all_inds, FILTER_PROOF)
    numeric_inds = framework.filter_indicators(all_inds, FILTER_NUMERIC)
    biblio_inds = framework.filter_indicators(all_inds, FILTER_BIBLIO)
    all_filtered = framework.filter_indicators(all_inds, FILTER_ALL)

    assert len(proof_inds) == 186
    assert len(numeric_inds) == 25
    assert len(biblio_inds) == 47
    assert len(all_filtered) == 260


def test_numeric_filter_strictly_excludes_bibliometrics(framework):
    """Verify that numerical data filter strictly excludes bibliometrics and external metrics."""
    all_inds = [ind for s in range(1, 18) for ind in framework.get_indicators_for_sdg(s)]
    numeric_inds = framework.filter_indicators(all_inds, FILTER_NUMERIC)

    for ind in numeric_inds:
        assert ind.get("type") != "bibliometric", f"Bibliometric indicator {ind['indicator_id']} leaked into numeric filter"
        assert ind.get("type") != "external_metric", f"External metric {ind['indicator_id']} leaked into numeric filter"
        assert ind.get("type") in ("quantitative", "mixed") or "fields" in ind


def test_bibliometrics_consultation_filter(framework):
    """Verify that bibliometric filter returns all 47 bibliometric indicators."""
    all_inds = [ind for s in range(1, 18) for ind in framework.get_indicators_for_sdg(s)]
    biblio_inds = framework.filter_indicators(all_inds, FILTER_BIBLIO)

    assert len(biblio_inds) == 47
    for ind in biblio_inds:
        assert ind.get("type") == "bibliometric"


def test_mixed_indicators_handled_in_both_proof_and_numeric(framework):
    """Verify that mixed indicators requiring evidence and figures appear in both proof and numeric filters."""
    mixed_ind = {
        "indicator_id": "99.2.1",
        "name": "Mixed Policy and Numbers",
        "type": "mixed",
        "fields": ["Field A", "Field B"],
        "requires_evidence": True
    }
    sample = [mixed_ind]

    in_proof = framework.filter_indicators(sample, FILTER_PROOF)
    in_numeric = framework.filter_indicators(sample, FILTER_NUMERIC)
    in_biblio = framework.filter_indicators(sample, FILTER_BIBLIO)
    in_all = framework.filter_indicators(sample, FILTER_ALL)

    assert len(in_proof) == 1
    assert len(in_numeric) == 1
    assert len(in_biblio) == 0
    assert len(in_all) == 1


def test_quantitative_indicator_with_evidence_required(framework):
    """Verify that a quantitative indicator with requires_evidence: True is included in proof filter."""
    quant_proof = {
        "indicator_id": "99.3.1",
        "name": "Quantitative with Evidence Required",
        "type": "quantitative",
        "fields": ["Total", "Target"],
        "requires_evidence": True
    }
    sample = [quant_proof]

    assert len(framework.filter_indicators(sample, FILTER_PROOF)) == 1
    assert len(framework.filter_indicators(sample, FILTER_NUMERIC)) == 1
    assert len(framework.filter_indicators(sample, FILTER_BIBLIO)) == 0


def test_sdg9_edge_case_no_proof_indicators(framework):
    """In SDG 9, there are 0 qualitative indicators requiring evidence."""
    sdg9_inds = framework.get_indicators_for_sdg(9)
    assert len(sdg9_inds) == 4

    proof_inds = framework.filter_indicators(sdg9_inds, FILTER_PROOF)
    assert len(proof_inds) == 0  # No proof indicators in SDG 9

    numeric_inds = framework.filter_indicators(sdg9_inds, FILTER_NUMERIC)
    assert len(numeric_inds) == 2  # 9.3.1, 9.4.1

    biblio_inds = framework.filter_indicators(sdg9_inds, FILTER_BIBLIO)
    assert len(biblio_inds) == 1  # 9.1.1

    all_inds = framework.filter_indicators(sdg9_inds, FILTER_ALL)
    assert len(all_inds) == 4  # 9.1.1, 9.2.1, 9.3.1, 9.4.1


def test_sdg17_edge_case_no_numeric_indicators(framework):
    """In SDG 17, there are 0 quantitative indicators to be entered by university."""
    sdg17_inds = framework.get_indicators_for_sdg(17)
    assert len(sdg17_inds) == 28

    proof_inds = framework.filter_indicators(sdg17_inds, FILTER_PROOF)
    assert len(proof_inds) == 25

    numeric_inds = framework.filter_indicators(sdg17_inds, FILTER_NUMERIC)
    assert len(numeric_inds) == 0

    biblio_inds = framework.filter_indicators(sdg17_inds, FILTER_BIBLIO)
    assert len(biblio_inds) == 2

    all_inds = framework.filter_indicators(sdg17_inds, FILTER_ALL)
    assert len(all_inds) == 28


def test_bilingual_filter_options(framework):
    """Verify that English filter names return identical results to French filter names."""
    all_inds = [ind for s in range(1, 18) for ind in framework.get_indicators_for_sdg(s)]

    # Proof
    fr_proof = framework.filter_indicators(all_inds, FILTER_PROOF)
    en_proof = framework.filter_indicators(all_inds, "Requiring documentary evidence")
    assert len(fr_proof) == len(en_proof) == 186

    # Numeric
    fr_num = framework.filter_indicators(all_inds, FILTER_NUMERIC)
    en_num = framework.filter_indicators(all_inds, "Numerical data to be provided by university")
    assert len(fr_num) == len(en_num) == 25

    # Biblio
    fr_bib = framework.filter_indicators(all_inds, FILTER_BIBLIO)
    en_bib = framework.filter_indicators(all_inds, "Bibliometric data — consultation only")
    assert len(fr_bib) == len(en_bib) == 47

    # All
    fr_all = framework.filter_indicators(all_inds, FILTER_ALL)
    en_all = framework.filter_indicators(all_inds, "All indicators")
    assert len(fr_all) == len(en_all) == 260


def test_clean_state_reset_simulation():
    """Simulate the dynamic reset logic when switching filters or SDGs."""
    # When user was on a bibliometric indicator (17.1.1) and switches to proof filter
    labels_proof = ["17.2.1 : Relations", "17.2.2 : Publications", "17.2.4 : Participation"]
    active_indicator_id = "17.1.1"

    # Search for active_indicator_id in new labels
    target_idx = 0
    for idx, lbl in enumerate(labels_proof):
        if lbl.startswith(f"{active_indicator_id} :"):
            target_idx = idx
            break

    # Since 17.1.1 is not in labels_proof, target_idx remains cleanly 0
    assert target_idx == 0
    assert labels_proof[target_idx] == "17.2.1 : Relations"

    # When user was on 17.2.4 and switches to 'All indicators'
    labels_all = ["17.1.1 : Scopus", "17.2.1 : Relations", "17.2.4 : Participation"]
    active_indicator_id = "17.2.4"
    target_idx = 0
    for idx, lbl in enumerate(labels_all):
        if lbl.startswith(f"{active_indicator_id} :"):
            target_idx = idx
            break

    # 17.2.4 is preserved!
    assert target_idx == 2
    assert labels_all[target_idx] == "17.2.4 : Participation"
