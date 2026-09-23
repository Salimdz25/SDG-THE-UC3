"""Tests for OCR zero-hallucination and document ingestion security."""

import pytest
from pathlib import Path
from unittest.mock import patch

from src.ingestion.ocr_engine import UC3MultilingualOCREngine
from src.ingestion.doc_parser import DocumentParser


def test_ocr_returns_ocr_indisponible_when_tesseract_missing(tmp_path):
    dummy_img = tmp_path / "scan.png"
    dummy_img.write_bytes(b"dummy image bytes")

    engine = UC3MultilingualOCREngine()
    engine._tesseract_available = False

    res = engine.process_image(dummy_img)
    assert res["status"] == "OCR_INDISPONIBLE"
    assert res["text"] == ""
    assert "simulated" not in res.get("status", "")
    assert "[Contenu extrait" not in res.get("text", "")


def test_doc_parser_rejects_legacy_doc(tmp_path):
    old_doc = tmp_path / "archive.doc"
    old_doc.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")  # OLE header

    parser = DocumentParser()
    with pytest.raises(ValueError) as excinfo:
        parser.parse_file(old_doc)
    assert "Word 97-2003 (.doc)" in str(excinfo.value)


def test_doc_parser_rejects_oversized_file(tmp_path):
    huge_file = tmp_path / "huge.txt"
    huge_file.write_text("Hello World")

    parser = DocumentParser(max_file_size_mb=0.000001)  # ~1 byte limit
    with pytest.raises(ValueError) as excinfo:
        parser.parse_file(huge_file)
    assert "Taille de fichier excessive" in str(excinfo.value)
