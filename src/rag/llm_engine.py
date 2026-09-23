"""
Moteur d'Évaluation LLM Réel - THE Sustainability Impact Ratings 2027
Université Constantine 3 (UC3) Salah Boubnider

Utilise l'API Gemini (google-genai) pour auditer les preuves textuelles et documentaires.
Applique un prompt système institutionnel strict sans hallucination.
"""

import os
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime

class RealLLMEvaluator:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        raw_key = (api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
        # Nettoyer les guillemets et espaces accidentels
        raw_key = raw_key.strip('"').strip("'").strip()
        self.api_key = raw_key if raw_key else None
        self.model_name = model_name
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[!] Erreur d'initialisation du client Gemini: {e}")

    def is_configured(self) -> bool:
        return self.client is not None and bool(self.api_key)

    def test_connection(self) -> Dict[str, Any]:
        """Teste la validité de la clé API avec un appel minimal."""
        if not self.is_configured():
            return {"valid": False, "message": "Aucune clé API renseignée."}
        try:
            # Test léger avec gemini-2.5-flash ou fallback
            resp = self.client.models.generate_content(
                model=self.model_name,
                contents="Réponds par le mot: OK"
            )
            if resp and resp.text:
                return {"valid": True, "message": f"Clé API valide ! Modèle '{self.model_name}' opérationnel."}
            return {"valid": False, "message": "Réponse vide de l'API."}
        except Exception as e:
            return {"valid": False, "message": str(e)}

    def evaluate_evidence_with_llm(
        self,
        indicator_id: str,
        indicator_name: str,
        indicator_definition: str,
        max_points: float,
        evidence_text: str,
        source_url_or_path: str,
        target_year: int = 2025,
        is_policy_bonus_eligible: bool = False
    ) -> Dict[str, Any]:
        """
        Appelle le LLM réel pour analyser la preuve soumise par l'utilisateur.
        """
        if not self.is_configured():
            return {
                "error": "CLÉ_API_MANQUANTE",
                "message": "Veuillez fournir une clé API Gemini (Google AI Studio) pour activer l'évaluation par LLM réel."
            }

        # Prompt d'évaluation institutionnel THE 2027
        system_instruction = f"""Tu es un auditeur expert et impartial du classement international Times Higher Education (THE) Sustainability Impact Ratings 2027, spécialisé dans l'évaluation des universités (notamment l'Université Constantine 3 Salah Boubnider - UC3).

RÈGLES IMPÉRATIVES DE LA MÉTHODOLOGIE THE 2027 :
1. RÈGLE D'OR ZÉRO-HALLUCINATION : Ne jamais inventer ou supposer une information absente. Si un chiffre, une date ou un fait n'est pas explicitement écrit dans la preuve, indique clairement son absence.
2. PERTINENCE THÉMATIQUE STRICTE (CRUCIAL & ÉLIMINATOIRE) :
   - Le texte soumis PEUT être totalement hors-sujet ou sans rapport avec l'indicateur audité (par exemple : un horaire de transport, un menu, une annonce d'examen, du sport, ou un sujet d'un autre ODD).
   - La simple présence des mots 'université', 'Constantine', 'faculté' ou d'une date NE CONSTITUE EN AUCUN CAS une preuve valable.
   - Si le texte ne traite pas DIRECTEMENT et SPÉCIFIQUEMENT du sujet exigé par l'indicateur [{indicator_id} : {indicator_name}], tu DOIS IMPÉRATIVEMENT :
     * Mettre quality = "not_relevant"
     * Mettre the_points_earned = 0.0
     * Mettre the_percentage = 0.0
     * Mettre status_category = "Absence de donnée"
     * Mettre proposed_action = "rejeter"
     * Dans "gap_or_alert", expliquer sans complaisance pourquoi le texte n'a AUCUN rapport avec l'indicateur.
3. ANNÉE DE RÉFÉRENCE : L'année cible obligatoire pour cette édition est {target_year}. Si la donnée date d'avant {target_year}, signale une anomalie temporelle (sauf pour les politiques où une révision 2022-2026 est valorisée).
4. EXIGENCE D'AUTOSUFFISANCE (SELF-CONTAINED) : L'auditeur (IA ou humain) ne clique sur aucun lien supplémentaire. Si la preuve est un répertoire ou une simple liste de liens sans contenu explicatif direct, elle DOIT ÊTRE REJETÉE (0 point pour la preuve).
5. PREUVE PUBLIQUE : Si la source est une URL web directe et publique (ex: univ-constantine3.dz), elle est publique (1 pt). Si la preuve provient d'un document local ou attaché (PDF/Word/Excel interne), THE l'évalue AUTOMATIQUEMENT comme NON PUBLIQUE (0 pt pour l'accès public).
6. BARÈME DE QUALITÉ DE LA PREUVE (UNIQUEMENT SI LE TEXTE EST PERTINENT) :
   - 'specific' (1.0 point) : Preuve directe, chiffrée, contextualisée et démontrant exactement l'activité requise.
   - 'general' (0.5 point) : Mention générale sans données probantes suffisantes.
   - 'not_relevant' (0.0 point) : Hors-sujet ou rejeté (0 point total).

INDICATEUR AUDITÉ :
- ID : {indicator_id}
- Titre : {indicator_name}
- Exigence officielle THE 2027 : {indicator_definition}
- Points max possibles : {max_points}
- Éligible au bonus politique révisée 2022-2026 : {is_policy_bonus_eligible}

SOURCE DE LA PREUVE :
- Source déclarée : {source_url_or_path}

TEXTE DE LA PREUVE À ÉVALUER :
\"\"\"
{evidence_text}
\"\"\"

Tu dois répondre UNIQUEMENT par un objet JSON valide (sans balises markdown superflues) respectant rigoureusement ce schéma :
{{
  "information_found": "Synthèse factuelle exacte et concise de ce qui est présent dans le texte",
  "detected_year": 2025 ou null,
  "justifying_quote": "Citation textuelle exacte (verbatim) de 1 à 3 phrases justifiant l'évaluation",
  "uc3_entity": "Entité identifiée (Rectorat, Faculté de..., Laboratoire..., ou 'Non identifiée')",
  "quality": "specific" ou "general" ou "not_relevant",
  "quality_justification": "Explication détaillée du choix de la qualité",
  "is_public": true ou false,
  "is_self_contained": true ou false,
  "is_link_farm": true ou false,
  "confidence": "élevée" ou "moyenne" ou "faible",
  "status_category": "Information vérifiée" ou "Inférence" ou "Information à confirmer" ou "Absence de donnée",
  "gap_or_alert": "Explication des lacunes, contradictions, pièces jointes non publiques ou répertoires de liens",
  "proposed_action": "valider" ou "publier" ou "compléter" ou "vérifier" ou "rejeter",
  "the_points_earned": 0.0 à {max_points},
  "the_max_points": {max_points},
  "the_percentage": 0.0 à 100.0,
  "recommendations": "Conseil méthodologique concret pour l'équipe UC3 pour maximiser les points"
}}
"""

        try:
            import time
            from google.genai import types

            # Modèles ordonnés avec fallbacks résilients
            models_to_try = []
            for m in [self.model_name, "gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro"]:
                if m and m not in models_to_try:
                    models_to_try.append(m)

            response_text = None
            last_err = None

            config = types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )

            for mod in models_to_try:
                # 2 tentatives par modèle en cas de pic temporaire 503
                for attempt in range(2):
                    try:
                        response = self.client.models.generate_content(
                            model=mod,
                            contents=system_instruction,
                            config=config
                        )
                        if response and response.text:
                            response_text = response.text
                            self.model_name = mod
                            break
                    except Exception as e_mod:
                        last_err = e_mod
                        err_msg = str(e_mod).lower()
                        # Si pic de demande 503, attendre 2 secondes avant nouvelle tentative
                        if "503" in err_msg or "unavailable" in err_msg or "high demand" in err_msg:
                            time.sleep(2.0)
                            continue
                        else:
                            break  # Passer au modèle suivant
                if response_text:
                    break

            if not response_text:
                raise RuntimeError(f"Échec de l'appel LLM Gemini avec les modèles testés : {last_err}")

            # Nettoyage du JSON éventuel
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()

            parsed = json.loads(clean_text)
            parsed["engine_used"] = "LLM Réel (Google Gemini)"
            return parsed

        except Exception as e:
            return {
                "error": "ERREUR_EXECUTION_LLM",
                "message": f"Erreur lors de l'exécution du modèle LLM : {str(e)}"
            }
