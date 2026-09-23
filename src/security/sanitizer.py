"""
Module de Sécurité et d'Anonymisation des Données (PII & Confidentialité)
Université Constantine 3 (UC3) Salah Boubnider

Protège les données institutionnelles et personnelles avant tout envoi vers un LLM externe :
1. Masquage PII (Emails, Téléphones algériens et internationaux, NIN / Matricules, RIB / CCP).
2. Classification automatique (PUBLIC, INTERNE, CONFIDENTIEL, SECRET).
3. Blocage automatique de la transmission LLM pour documents confidentiels sans accord explicite.
"""

import re
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional


class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNE = "INTERNE"
    CONFIDENTIEL = "CONFIDENTIEL"
    SECRET = "SECRET"


# Marqueurs de confidentialité stricts
CONFIDENTIAL_PATTERNS = [
    (r"(?i)\b(?:strictement\s+confidentiel|secret\s+défense|très\s+secret)\b", DataClassification.SECRET),
    (r"(?i)\b(?:confidentiel|diffusion\s+restreinte|ne\s+pas\s+diffuser|usage\s+interne\s+exclusif)\b", DataClassification.CONFIDENTIEL),
    (r"(?i)\b(?:pv\s+de\s+délibération|procès-verbal\s+de\s+délibération|notes\s+d'examen\s+nominatives)\b", DataClassification.CONFIDENTIEL),
    (r"(?i)\b(?:dossier\s+médical|secret\s+médical|fiche\s+médicale)\b", DataClassification.CONFIDENTIEL),
    (r"(?i)\b(?:note\s+de\s+service\s+interne|circulaire\s+interne|compte-rendu\s+interne)\b", DataClassification.INTERNE),
]


def classify_document(text: str) -> Tuple[DataClassification, List[str]]:
    """
    Détermine le niveau de confidentialité d'un texte basé sur des marqueurs institutionnels.
    Retourne la classification la plus restrictive et les motifs trouvés.
    """
    reasons = []
    current_level = DataClassification.PUBLIC

    level_order = {
        DataClassification.PUBLIC: 0,
        DataClassification.INTERNE: 1,
        DataClassification.CONFIDENTIEL: 2,
        DataClassification.SECRET: 3,
    }

    for pattern, level in CONFIDENTIAL_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            reasons.append(f"Mot-clé détecté : '{matches[0]}'")
            if level_order[level] > level_order[current_level]:
                current_level = level

    return current_level, reasons


def mask_pii(text: str) -> Tuple[str, Dict[str, int]]:
    """
    Masque les données à caractère personnel (PII) dans le texte :
    - Emails
    - Téléphones (+213, 05/06/07, fixes, internationaux)
    - Numéros d'Identification Nationale (NIN 18 chiffres) et Matricules étudiants
    - RIB bancaires, CCP, IBAN
    """
    counts = {
        "emails": 0,
        "phones": 0,
        "ids_or_matricules": 0,
        "financial_accounts": 0,
    }

    sanitized = text

    # 1. Emails
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    emails_found = re.findall(email_pattern, sanitized)
    if emails_found:
        counts["emails"] = len(emails_found)
        sanitized = re.sub(email_pattern, "[EMAIL_MASQUÉ]", sanitized)

    # 2. RIB, IBAN, CCP (banque algérienne ou internationale)
    rib_iban_pattern = (
        r"(?i)\b(?:rib|iban|ccp|compte\s*(?:courant|bancaire)?)\s*[:#\-]?\s*"
        r"(?:[A-Z]{2}\d{2}[A-Z0-9]{10,30}|\d{10,24})\b"
    )
    ribs_found = re.findall(rib_iban_pattern, sanitized)
    if ribs_found:
        counts["financial_accounts"] = len(ribs_found)
        sanitized = re.sub(rib_iban_pattern, "[RIB_CCP_MASQUÉ]", sanitized)

    # 3. NIN (Numéro d'Identification Nationale Algérien - 18 chiffres) & Matricules explicites
    nin_pattern = r"\b\d{18}\b"
    nins_found = re.findall(nin_pattern, sanitized)
    matricule_pattern = r"(?i)\b(?:matricule|nin|nss|cin|id)\s*[:#\-]?\s*([A-Za-z0-9\-_]{6,20})\b"
    mats_found = re.findall(matricule_pattern, sanitized)

    total_ids = len(nins_found) + len(mats_found)
    if total_ids > 0:
        counts["ids_or_matricules"] = total_ids
        sanitized = re.sub(nin_pattern, "[IDENTIFIANT_MASQUÉ]", sanitized)
        sanitized = re.sub(matricule_pattern, "[IDENTIFIANT_MASQUÉ]", sanitized)

    # 4. Téléphones (Algérie +213 / 05, 06, 07, 031, fixes, et numéros internationaux)
    phone_pattern = (
        r"(?:(?:\+|00)213[\s.-]?(?:\(0\))?|0)[1-9](?:[\s.-]?\d{2}){3,4}\b|"
        r"(?:\+\d{1,3}[\s.-]?)?\(?\d{2,4}\)?(?:[\s.-]?\d{2,4}){2,3}\b"
    )
    phones_found = re.findall(phone_pattern, sanitized)
    if phones_found:
        counts["phones"] = len(phones_found)
        sanitized = re.sub(phone_pattern, "[TÉL_MASQUÉ]", sanitized)

    return sanitized, counts


def sanitize_for_llm(text: str, allow_confidential: bool = False) -> Dict[str, Any]:
    """
    Analyse complète de sécurité avant transmission LLM :
    - Classification du document.
    - Anonymisation PII systématique.
    - Blocage de sécurité si le document est CONFIDENTIEL ou SECRET sans exemption explicite.
    """
    classification, reasons = classify_document(text)
    sanitized_text, masked_counts = mask_pii(text)

    is_blocked = False
    warning_msg = None

    if classification in (DataClassification.CONFIDENTIEL, DataClassification.SECRET) and not allow_confidential:
        is_blocked = True
        warning_msg = (
            f"SÉCURITÉ : Document classifié '{classification.value}' en raison de : "
            f"{', '.join(reasons)}. "
            "Transmission à l'IA externe bloquée conformément à la politique de protection des données institutionnelles."
        )

    return {
        "sanitized_text": sanitized_text,
        "classification": classification.value,
        "reasons": reasons,
        "entities_masked": masked_counts,
        "total_masked": sum(masked_counts.values()),
        "blocked_for_llm": is_blocked,
        "warning": warning_msg,
    }
