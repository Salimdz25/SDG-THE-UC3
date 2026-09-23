"""Unit tests for PII and Confidentiality Sanitizer."""

import pytest
from src.security.sanitizer import (
    DataClassification,
    classify_document,
    mask_pii,
    sanitize_for_llm,
)


def test_mask_emails():
    text = "Pour toute question, contactez le recteur à recteur@univ-constantine3.dz ou admin.support@uc3.edu.dz."
    sanitized, counts = mask_pii(text)
    assert counts["emails"] == 2
    assert "recteur@univ-constantine3.dz" not in sanitized
    assert "admin.support@uc3.edu.dz" not in sanitized
    assert "[EMAIL_MASQUÉ]" in sanitized


def test_mask_algerian_phone_numbers():
    text = "Téléphone fixe Constantine: 031 81 12 34, Mobile: 0661 23 45 67, Intl: +213 550 11 22 33."
    sanitized, counts = mask_pii(text)
    assert counts["phones"] >= 3
    assert "031 81 12 34" not in sanitized
    assert "0661 23 45 67" not in sanitized
    assert "+213 550 11 22 33" not in sanitized
    assert "[TÉL_MASQUÉ]" in sanitized


def test_mask_nin_and_matricules():
    text = "Étudiant matricule MAT-202131045678 avec NIN 123456789012345678 inscrit en Master."
    sanitized, counts = mask_pii(text)
    assert counts["ids_or_matricules"] >= 2
    assert "123456789012345678" not in sanitized
    assert "MAT-202131045678" not in sanitized
    assert "[IDENTIFIANT_MASQUÉ]" in sanitized


def test_mask_financial_accounts():
    text = "Virement effectué sur le RIB 00799999000123456789 ou CCP 12345678."
    sanitized, counts = mask_pii(text)
    assert counts["financial_accounts"] >= 1
    assert "00799999000123456789" not in sanitized
    assert "[RIB_CCP_MASQUÉ]" in sanitized


def test_document_classification():
    pub_text = "L'Université Constantine 3 lance son rapport public sur le climat."
    c_pub, _ = classify_document(pub_text)
    assert c_pub == DataClassification.PUBLIC

    intern_text = "Note de service interne relative aux horaires de navette."
    c_intern, _ = classify_document(intern_text)
    assert c_intern == DataClassification.INTERNE

    conf_text = "Document Confidentiel : PV de délibération du conseil de discipline."
    c_conf, reasons = classify_document(conf_text)
    assert c_conf == DataClassification.CONFIDENTIEL
    assert len(reasons) >= 1

    secret_text = "Document Strictement Confidentiel concernant la sécurité du campus."
    c_sec, _ = classify_document(secret_text)
    assert c_sec == DataClassification.SECRET


def test_sanitize_blocks_confidential_by_default():
    conf_doc = (
        "CONFIDENTIEL : Données nominatives et PV de délibération. "
        "Contact: responsable@univ-constantine3.dz."
    )
    res = sanitize_for_llm(conf_doc, allow_confidential=False)
    assert res["blocked_for_llm"] is True
    assert res["classification"] == DataClassification.CONFIDENTIEL.value
    assert "responsable@univ-constantine3.dz" not in res["sanitized_text"]
    assert res["warning"] is not None


def test_sanitize_allows_confidential_when_explicitly_authorized():
    conf_doc = (
        "CONFIDENTIEL : Accord exceptionnel de transmission. "
        "Contact: responsable@univ-constantine3.dz."
    )
    res = sanitize_for_llm(conf_doc, allow_confidential=True)
    assert res["blocked_for_llm"] is False
    assert "responsable@univ-constantine3.dz" not in res["sanitized_text"]
    assert res["total_masked"] >= 1
