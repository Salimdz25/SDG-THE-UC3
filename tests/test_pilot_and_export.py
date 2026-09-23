import pytest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.pilot.sdg17_pilot import SDG17PilotEngine
from src.export.exporter import UC3ReportExporter

def test_sdg17_pilot_execution():
    pilot = SDG17PilotEngine()
    results = pilot.run_pilot()

    assert results["sdg_number"] == 17
    assert results["is_mandatory"] is True
    assert results["total_indicators"] > 0
    assert len(results["fiches"]) == results["total_indicators"]
    assert "status_summary" in results
    assert "Information vérifiée" in results["status_summary"]

def test_excel_and_word_exports(tmp_path):
    pilot = SDG17PilotEngine()
    results = pilot.run_pilot()
    exporter = UC3ReportExporter()

    excel_file = tmp_path / "test_export.xlsx"
    word_file = tmp_path / "test_export.docx"

    excel_out = exporter.export_excel(results["fiches"], excel_file)
    word_out = exporter.export_word(results, word_file)

    assert Path(excel_out).exists()
    assert Path(excel_out).stat().st_size > 0
    assert Path(word_out).exists()
    assert Path(word_out).stat().st_size > 0
