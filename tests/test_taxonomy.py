import pytest
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.methodology.the_2027_framework import THE2027Framework

def test_taxonomy_completeness():
    framework = THE2027Framework()
    sdgs = framework.get_all_sdgs()
    
    # Vérifier que les 17 ODD sont présents
    assert len(sdgs) == 17, f"Attendu 17 ODD, trouvé {len(sdgs)}"
    for i in range(1, 18):
        assert str(i) in sdgs, f"L'ODD {i} est manquant dans le référentiel"

def test_mandatory_sdg_17():
    framework = THE2027Framework()
    sdg17 = framework.get_sdg(17)
    assert sdg17 is not None
    assert "Partnerships" in sdg17["name"]
    
    # Indicateurs 17.2.1, 17.2.2, etc.
    ind = framework.get_indicator("17.2.1")
    assert ind is not None
    assert ind["max_points"] == 3
    assert ind["year"] == 2025

def test_overall_rank_calculation():
    framework = THE2027Framework()
    mock_scores = {
        17: 80.0, # Obligatoire: 80 * 0.22 = 17.6
        3: 90.0,  # Top 1: 90 * 0.26 = 23.4
        9: 85.0,  # Top 2: 85 * 0.26 = 22.1
        4: 80.0,  # Top 3: 80 * 0.26 = 20.8
        1: 70.0,  # Pas retenu
        2: 60.0   # Pas retenu
    }
    # Total attendu = 17.6 + 23.4 + 22.1 + 20.8 = 83.9
    res = framework.compute_overall_rank_score(mock_scores)
    assert res["is_eligible_overall"] is True
    assert res["overall_score"] == 83.9
    assert len(res["top_3_sdgs"]) == 3
    assert res["top_3_sdgs"][0][0] == 3
