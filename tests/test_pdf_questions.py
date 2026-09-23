"""Tests for official PDF question extraction (THE Sustainability Impact Ratings 2027)."""

import os
from pathlib import Path
import pytest

from src.methodology.pdf_questions import indicator_question, DEFAULT_PDF_FALLBACK


def _get_pdf_path() -> str:
    path = os.environ.get("THE_2027_PDF") or DEFAULT_PDF_FALLBACK
    if not Path(path).is_file():
        pytest.skip(f"Official PDF not found at {path}")
    return path


@pytest.mark.parametrize("indicator_id", ["1.3.1", "4.3.5", "11.2.2", "17.2.4", "17.3.5"])
def test_extract_indicators_across_sdgs(indicator_id: str):
    pdf = _get_pdf_path()
    text = indicator_question(pdf, indicator_id)
    assert text.startswith("PDF officiel 2027"), f"Failed prefix for {indicator_id}"
    assert indicator_id in text, f"Indicator ID {indicator_id} missing from extracted text"
    assert len(text) > 100, f"Extracted text too short for {indicator_id}: {len(text)} chars"


def test_grouped_sdg17_indicators():
    pdf = _get_pdf_path()
    for target_sdg in [1, 5, 13, 17]:
        ind_id = f"17.3.{target_sdg}"
        text = indicator_question(pdf, ind_id)
        assert f"17.3.{target_sdg}" in text
        assert "Publication of SDG reports" in text
        assert "Year: 2025" in text


def test_missing_pdf_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        indicator_question("non_existent_path_to_pdf_file.pdf", "1.3.1")


def test_invalid_indicator_raises_value_error():
    pdf = _get_pdf_path()
    with pytest.raises(ValueError):
        indicator_question(pdf, "99.99.99")
