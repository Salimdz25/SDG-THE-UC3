"""Read an indicator's actual question from the licensed local 2027 methodology PDF."""

import hashlib
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_PDF_CACHE: Dict[str, Tuple[float, List[str], str]] = {}

DEFAULT_PDF_FALLBACK = r"C:\Users\hp pavillon\Downloads\THE.SustainabilityImpactRatings.METHODOLOGY.2027.v1.2.pdf"
OFFICIAL_2027_PDF_SHA256 = "f3e8e4753cff3d00605a4858f42db7b5542d5fc506b45b01cbc9868e739934a4"


def resolve_pdf_path(pdf_path: str | Path = "") -> Path:
    """Resolve the PDF path dynamically across environment variables, project directories, and fallbacks."""
    if pdf_path:
        p = Path(pdf_path)
        if p.is_file():
            return p
        raise FileNotFoundError(f"Fichier PDF méthodologique spécifié introuvable : {pdf_path}")

    env_path = os.environ.get("THE_2027_PDF")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p

    # Search in project methodology folders
    project_root = Path(__file__).resolve().parent.parent.parent
    data_meth = project_root / "data" / "methodology"
    if data_meth.is_dir():
        for f in data_meth.glob("*.pdf"):
            if f.is_file():
                return f

    # Fallback path
    fallback = Path(DEFAULT_PDF_FALLBACK)
    if fallback.is_file():
        return fallback

    raise FileNotFoundError(
        "Fichier PDF méthodologique introuvable. "
        "Veuillez définir la variable d'environnement THE_2027_PDF avec le chemin absolu du document officiel "
        "'THE Sustainability Impact Ratings Methodology 2027 v1.0'."
    )


def compute_pdf_sha256(pdf_path: Path) -> str:
    """Computes SHA-256 fingerprint of the methodology PDF for regulatory audit."""
    h = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _get_cleaned_pages(pdf_path: Path) -> Tuple[List[str], str]:
    """Cache extracted and cleaned pages by mtime to avoid repeatedly reading 190 pages."""
    from pypdf import PdfReader

    abs_key = str(pdf_path.resolve())
    mtime = pdf_path.stat().st_mtime
    if abs_key in _PDF_CACHE and _PDF_CACHE[abs_key][0] == mtime:
        return _PDF_CACHE[abs_key][1], _PDF_CACHE[abs_key][2]

    sha256 = compute_pdf_sha256(pdf_path)
    reader = PdfReader(str(pdf_path))
    pages: List[str] = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        # Nettoyer les en-têtes et pieds de page répétitifs 2026 et 2027
        txt = re.sub(r"THE SUSTAINABILITY IMPACT RATINGS METHODOLOGY 202[67]\s*\|\s*\d+", "", txt)
        pages.append(txt)

    _PDF_CACHE[abs_key] = (mtime, pages, sha256)
    return pages, sha256


def indicator_question(pdf_path: str | Path = "", indicator_id: str = "") -> str:
    """
    Extrait la question intégrale, les précisions et les conditions officielles
    d'un indicateur qualitatif depuis le PDF THE Sustainability Impact Ratings Methodology 2027.
    """
    path = resolve_pdf_path(pdf_path)
    pages_text, pdf_sha = _get_cleaned_pages(path)

    # 1. Cas particulier ODD 17 : 17.3.1 à 17.3.17 regroupés dans le PDF officiel (Page 155 / Index 154)
    parts = indicator_id.split(".")
    if len(parts) == 3 and parts[0] == "17" and parts[1] == "3":
        try:
            sdg_target_num = int(parts[2])
            if 1 <= sdg_target_num <= 17 and len(pages_text) > 154:
                p155 = pages_text[154]
                match_17_3 = re.search(r"17\.3\.1\s+to\s+17\.3\.17[\s\S]*?Data submission guidance", p155)
                if match_17_3:
                    full_desc = match_17_3.group(0).strip()
                    return (
                        f"PDF officiel 2027 (SHA-256: {pdf_sha[:12]}...), page 155:\n"
                        f"Indicateur {indicator_id} — Publication de rapport ODD (spécifiquement pour l'ODD {sdg_target_num})\n\n"
                        f"{full_desc}"
                    )
        except ValueError:
            pass

    # 2. Cas général : recherche de la définition formelle de l'indicateur
    escaped = re.escape(indicator_id)
    # L'indicateur commence au début de sa ligne, seul ou suivi d'un titre (pas 'Indicator:' ni '#')
    heading = re.compile(rf"(?m)^\s*{escaped}\s*$|^\s*{escaped}\s+(?!Indicator:)[A-Za-z]")
    next_heading = re.compile(
        r"(?m)^\s*(?:(?:1[0-7]|[1-9])\.\d+(?:\.\d+)?\s+[A-Z]|Data submission guidance|\d+(?:\.\d+)?%\s*in\s+SDG)"
    )

    for page_index, page_text in enumerate(pages_text):
        if page_index < 11:  # Ignorer la table des matières et la présentation générale
            continue

        for match in heading.finditer(page_text):
            snippet = page_text[match.start():]
            first_lines = snippet[:200]
            # Ignorer les tables de synthèse ou d'en-tête
            if "# Indicator" in first_lines or "Maximum \nscore" in first_lines or "Maximum score" in first_lines:
                continue

            # Valider qu'il s'agit bien de la définition de l'indicateur
            if "Year:" in snippet[:350] or "points based on:" in snippet[:1500] or "Up to" in snippet[:600]:
                combined = snippet + "\n" + (pages_text[page_index + 1] if page_index + 1 < len(pages_text) else "")
                end = next_heading.search(combined, len(indicator_id) + 3)
                excerpt = combined[:end.start() if end else 5000].strip()

                if len(excerpt) < 40:
                    raise ValueError(f"Question {indicator_id} trop courte pour être évaluée.")

                return f"PDF officiel 2027 (SHA-256: {pdf_sha[:12]}...), page {page_index + 1}:\n{excerpt}"

    raise ValueError(f"Question {indicator_id} introuvable dans le PDF officiel 2027.")
