"""
Script Principal d'Exécution - Assistant RAG UC3 (THE Impact Ratings 2027)
Université Constantine 3 Salah Boubnider

Commandes disponibles :
  python run_pipeline.py --pilot      : Exécute l'audit complet sur l'ODD 17
  python run_pipeline.py --export     : Génère les dossiers Excel et Word
  python run_pipeline.py --dashboard  : Lance le tableau de bord interactif Streamlit
"""

import argparse
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Configurer l'encodage de la console sous Windows pour UTF-8
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.pilot.sdg17_pilot import SDG17PilotEngine
from src.export.exporter import UC3ReportExporter

def run_pilot_audit():
    print("=" * 80)
    print(" UNIVERSITÉ CONSTANTINE 3 (UC3) - ASSISTANT RAG THE IMPACT RATINGS 2027")
    print(" Pilotage et Évaluation des Preuves de Durabilité")
    print("=" * 80)
    
    pilot = SDG17PilotEngine()
    results = pilot.run_pilot()

    print(f"\n[+] ODD Analysé : {results['sdg_name']}")
    print(f"[+] Année de référence cible : {results['target_year']}")
    print(f"[+] Nombre d'indicateurs traités : {results['total_indicators']}")
    print(f"[+] Points THE estimés : {results['total_points_earned']} / {results['max_possible_points']} pts")
    print(f"[+] Taux de complétude ODD 17 : {results['sdg_completion_percentage']}%\n")

    print("--- Répartition selon la règle Zéro-Hallucination ---")
    for status, cnt in results["status_summary"].items():
        print(f"  • {status:25} : {cnt}")

    print("\n--- Actions Prioritaires Recommandées ---")
    for action, cnt in results["actions_summary"].items():
        print(f"  • Action '{action.upper()}' : {cnt}")

    print("\n" + "=" * 80)
    print(" ÉCHANTILLON DES FICHES D'INDICATEURS EXTRAITES :")
    print("=" * 80)
    
    for f in results["fiches"][:4]:
        print(f"\n>> [{f['odd_indicator']}] {f['indicator_title']}")
        print(f"   - Statut       : {f['status_category']} (Confiance: {f['confidence'].upper()})")
        print(f"   - Information  : {f['information_found']}")
        print(f"   - Source       : {f['source_exact']} ({f['publicity'].upper()})")
        print(f"   - Points THE   : {f['the_points']} / {f['the_max_points']} pts")
        if "ATTENTION" in f["gap_or_alert"] or "REJET" in f["gap_or_alert"]:
            print(f"   - ⚠️ ALERTE     : {f['gap_or_alert']}")
        print(f"   - Action       : {f['proposed_action'].upper()}")

    return results

def run_exports(results=None):
    if results is None:
        pilot = SDG17PilotEngine()
        results = pilot.run_pilot()

    exporter = UC3ReportExporter()
    export_dir = ROOT_DIR / "exports"
    export_dir.mkdir(exist_ok=True)

    excel_file = export_dir / "UC3_THE_Impact_2027_ODD17_Fiches.xlsx"
    word_file = export_dir / "UC3_THE_Impact_2027_Rapport_Officiel.docx"

    excel_path = exporter.export_excel(results["fiches"], excel_file)
    word_path = exporter.export_word(results, word_file)

    print("\n[+] Exports officiels générés avec succès :")
    print(f"    Excel : {excel_path}")
    print(f"    Word  : {word_path}")

def run_dashboard():
    dashboard_path = ROOT_DIR / "src" / "dashboard" / "app.py"
    print(f"\n[+] Lancement du tableau de bord Streamlit : {dashboard_path}")
    cmd = [sys.executable, "-m", "streamlit", "run", str(dashboard_path), "--server.headless=true"]
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="Assistant RAG UC3 pour THE Impact Ratings 2027")
    parser.add_argument("--pilot", action="store_true", help="Exécuter l'audit pilote sur l'ODD 17")
    parser.add_argument("--export", action="store_true", help="Générer les exports Excel et Word")
    parser.add_argument("--dashboard", action="store_true", help="Lancer l'application web Streamlit")

    args = parser.parse_args()

    if args.dashboard:
        run_dashboard()
    elif args.export:
        run_exports()
    elif args.pilot:
        run_pilot_audit()
    else:
        run_dashboard()

if __name__ == "__main__":
    main()
