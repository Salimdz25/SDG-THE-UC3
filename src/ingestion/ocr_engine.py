"""
Moteur OCR Multilingue (Français, Arabe, Anglais) pour documents administratifs UC3
Traite les arrêtés rectoraux, PV de délibérations, conventions scannées et affiches d'événements.
"""

from pathlib import Path
from typing import Dict, Any, Optional

class UC3MultilingualOCREngine:
    def __init__(self, languages: str = "fra+ara+eng"):
        self.languages = languages
        self._tesseract_available = False
        try:
            import pytesseract
            self._tesseract_available = True
        except ImportError:
            self._tesseract_available = False

    def is_ocr_ready(self) -> bool:
        return self._tesseract_available

    def process_image(self, image_path: str | Path) -> Dict[str, Any]:
        """
        Extrait le texte d'un document numérisé ou d'une affiche d'événement.
        """
        path = Path(image_path)
        if not path.exists():
            return {"error": f"Image non trouvée: {path}", "text": ""}

        if self._tesseract_available:
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(path)
                text = pytesseract.image_to_string(img, lang=self.languages)
                return {
                    "status": "success",
                    "source": str(path),
                    "languages_used": self.languages,
                    "text": text.strip()
                }
            except Exception as e:
                err_msg = str(e)
                if "tesseract is not installed" in err_msg.lower() or "tesseractnotfound" in err_msg.lower():
                    status_name = "OCR_INDISPONIBLE"
                else:
                    status_name = "error"
                return {
                    "status": status_name,
                    "error_message": f"Erreur lors de l'OCR Tesseract: {e}",
                    "text": ""
                }
        else:
            # Règle d'or : Zéro hallucination. Jamais de texte simulé ou inventé.
            return {
                "status": "OCR_INDISPONIBLE",
                "error_message": (
                    "Le moteur OCR (pytesseract / binaire Tesseract) n'est pas disponible sur ce système. "
                    "Impossible d'extraire automatiquement le contenu sans OCR opérationnel."
                ),
                "source": str(path),
                "text": ""
            }
