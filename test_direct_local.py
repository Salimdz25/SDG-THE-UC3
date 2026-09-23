"""
Testeur en Ligne de Commande Local - Audit des Indicateurs UC3 (THE 2027)
Université Constantine 3 Salah Boubnider

Permet d'évaluer instantanément une preuve sans navigateur web.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Encodage UTF-8 sous Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.methodology.the_2027_framework import THE2027Framework
from src.evaluation.the_evaluator import THEEvidenceEvaluator
from src.rag.extractor import UC3IndicatorExtractor
from src.export.exporter import UC3ReportExporter

def print_separator(title=""):
    print("\n" + "=" * 80)
    if title:
        print(f" {title}")
        print("=" * 80)

def run_local_evaluation(indicator_id: str, evidence_text: str, source_path: str, entity: str = "UC3"):
    framework = THE2027Framework()
    evaluator = THEEvidenceEvaluator(target_year=2025)
    extractor = UC3IndicatorExtractor(framework, evaluator)

    ind_meta = framework.get_indicator(indicator_id)
    if not ind_meta:
        print(f"[!] Erreur : Indicateur '{indicator_id}' introuvable dans le référentiel THE 2027.")
        return

    print_separator(f"AUDIT LOCAL THE 2027 : [{indicator_id}] {ind_meta.get('name')}")
    print(f"📘 Exigence officielle : {ind_meta.get('definition', '')}")
    print(f"📎 Source déclarée     : {source_path}")
    print(f"🏛️ Entité UC3           : {entity}")
    print(f"📄 Texte de la preuve   :\n\"{evidence_text.strip()}\"")
    print("-" * 80)

    # Simulation du chunk ingéré
    chunk = [{
        "text": evidence_text,
        "source_url_or_path": source_path,
        "entity": entity,
        "source_type": "LOCAL_INPUT",
        "is_public": source_path.startswith("http"),
        "date": "2025"
    }]

    fiche = extractor.extract_indicator_fiche(indicator_id, chunk)

    print("\n📋 RÉSULTATS DE LA FICHE D'ÉVALUATION :")
    print(f"  • Points THE obtenus     : {fiche.the_points} / {fiche.the_max_points} pts ({fiche.the_percentage}%)")
    print(f"  • Qualité de la preuve   : {fiche.quality.upper()}")
    print(f"  • Caractère Public       : {fiche.publicity.upper()}")
    print(f"  • Niveau de Confiance    : {fiche.confidence.upper()}")
    print(f"  • Catégorie de Fiabilité : {fiche.status_category}")
    print(f"  • Action Proposée        : {fiche.proposed_action.upper()}")

    if "ATTENTION" in fiche.gap_or_alert or "REJET" in fiche.gap_or_alert:
        print(f"\n  ⚠️ ALERTE THE 2027 :\n    {fiche.gap_or_alert}")
    else:
        print("\n  ✅ Autosuffisance : Conforme aux règles THE 2027.")

    print(f"\n  💬 Citation Justificative Verbatim :\n    {fiche.justifying_quote}")

    return fiche

def run_automated_scenarios():
    print_separator("EXÉCUTION DES SCÉNARIOS TYPES DE L'UNIVERSITÉ CONSTANTINE 3")

    # Scénario 1 : Preuve Conforme
    run_local_evaluation(
        indicator_id="17.2.2",
        evidence_text=(
            "Université Constantine 3 Salah Boubnider - 18 mai 2025. "
            "Le Rectorat de l'Université Constantine 3 a organisé le Colloque International sur le Dialogue Intersectoriel "
            "pour les ODD et la Transition Énergétique en présence de représentants du Ministère de l'Enseignement Supérieur, "
            "de l'Agence Nationale des Déchets (AND), de Sonelgaz et d'associations locales avec 180 participants."
        ),
        source_path="https://univ-constantine3.dz/colloque-odd-2025/",
        entity="Rectorat & Faculté Génie des Procédés UC3"
    )

    # Scénario 2 : Document Interne Non Public
    run_local_evaluation(
        indicator_id="17.2.1",
        evidence_text=(
            "Université Constantine 3 Salah Boubnider. "
            "Convention signée le 10 février 2025 entre le Recteur de l'UC3 et la Direction de l'Environnement "
            "de la Wilaya de Constantine pour l'assistance technique et l'élaboration du Plan Climat local."
        ),
        source_path="C:/Archives_Rectorat/Convention_Environnement_2025.pdf",
        entity="Rectorat UC3"
    )

    # Scénario 3 : Annuaire de Liens Rejeté par THE
    run_local_evaluation(
        indicator_id="17.2.4",
        evidence_text=(
            "Consultez les liens de nos partenaires internationaux : "
            "https://www.sdgaccord.org/members/ "
            "https://www.tethys-univ.org/ "
            "https://erasmus-plus.dz/ "
            "Veuillez cliquer sur les liens ci-dessus pour voir les détails de chaque accord."
        ),
        source_path="https://univ-constantine3.dz/liens-partenaires",
        entity="Service Relations Extérieures UC3"
    )

    # Scénario 4 : Absence de Donnée (Zéro-Hallucination)
    framework = THE2027Framework()
    evaluator = THEEvidenceEvaluator()
    extractor = UC3IndicatorExtractor(framework, evaluator)
    fiche_absent = extractor.extract_indicator_fiche("17.4.4", [])
    print_separator("SCÉNARIO 4 : ABSENCE DE DONNÉE (RÈGLE ZÉRO-HALLUCINATION)")
    print(f"Indicateur : 17.4.4 - Sustainability Literacy")
    print(f"Résultat   : {fiche_absent.status_category}")
    print(f"Contenu    : {fiche_absent.information_found}")
    print(f"Action     : {fiche_absent.proposed_action.upper()}")

if __name__ == "__main__":
    run_automated_scenarios()
