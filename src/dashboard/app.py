"""
Tableau de Bord Institutionnel - Université Constantine 3 (UC3) Salah Boubnider
Module Principal : 📥 Ingestion & Évaluation en Direct par LLM Réel
THE Sustainability Impact Ratings 2027 (v1.0)
"""

import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime

# Configuration du PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd

from src.methodology.the_2027_framework import THE2027Framework
from src.evaluation.the_evaluator import THEEvidenceEvaluator
from src.ingestion.doc_parser import DocumentParser
from src.ingestion.web_crawler import UC3WebCrawler
from src.ingestion.facebook_collector import FacebookInstitutionalCollector
from src.rag.llm_engine import RealLLMEvaluator
from src.export.exporter import UC3ReportExporter
from src.rag.models import IndicatorFiche

# Configuration de la page Streamlit
st.set_page_config(
    page_title="UC3 - Évaluation en Direct THE Impact 2027",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Chargement des ressources
@st.cache_resource
def get_framework():
    return THE2027Framework()

@st.cache_resource
def get_doc_parser():
    return DocumentParser()

@st.cache_resource
def get_web_crawler():
    return UC3WebCrawler()

@st.cache_resource
def get_fb_collector():
    return FacebookInstitutionalCollector()

framework = get_framework()
doc_parser = get_doc_parser()
web_crawler = get_web_crawler()
fb_collector = get_fb_collector()
exporter = UC3ReportExporter()

# --- SIDEBAR : CONFIGURATION DU LLM RÉEL ---
with st.sidebar:
    st.markdown("### 🏛️ Université Constantine 3")
    st.markdown("**Salah Boubnider**")
    st.caption("Assistant RAG - Audit THE Impact Ratings 2027")
    st.divider()

    st.markdown("#### 🤖 Configuration du Modèle LLM")
    env_gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    
    user_api_key = st.text_input(
        "Clé API Gemini (Google AI Studio) :",
        value=env_gemini_key,
        type="password",
        help="Obtenez une clé gratuite sur https://aistudio.google.com/ pour activer l'analyse neuronale réelle."
    )

    selected_model = st.selectbox(
        "Modèle LLM :",
        ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro"],
        index=0,
        help="gemini-2.0-flash est le modèle recommandé par Google AI Studio (rapide et très disponible)."
    )

    llm_evaluator = RealLLMEvaluator(api_key=user_api_key, model_name=selected_model)

    if st.button("🔌 Tester la Clé API"):
        if not user_api_key.strip():
            st.warning("Veuillez d'abord coller votre clé API.")
        else:
            with st.spinner("Vérification auprès de Google Gemini..."):
                t_res = llm_evaluator.test_connection()
                if t_res["valid"]:
                    st.success(f"✅ {t_res['message']}")
                else:
                    st.error(f"❌ Erreur : {t_res['message']}")
    
    if llm_evaluator.is_configured():
        st.success("🟢 **LLM Réel Connecté (Gemini)**")
    else:
        st.warning("🟡 **Mode Audit Local Actif**\n*(Saisissez votre clé Gemini ci-dessus pour activer le LLM réel)*")

    st.divider()
    st.markdown("#### 📜 Règles Méthodologiques THE")
    st.markdown("- **Année Cible :** `2025`")
    st.markdown("- **Preuve Publique :** URL directe = 1 pt / Fichier joint = 0 pt")
    st.markdown("- **Autosuffisance :** Annuaire de liens = Rejet")
    st.markdown("- **Zéro-Hallucination :** Absence de donnée formelle")

# --- EN-TÊTE PRINCIPAL ---
st.title("📥 Ingestion & Évaluation de Preuves en Direct (THE 2027)")
st.markdown(
    "Sélectionnez un indicateur parmi les **17 ODD**, soumettez une preuve (texte, fichier PDF/Word/Excel ou URL), "
    "et laissez l'auditeur LLM analyser la conformité selon le barème officiel."
)
st.divider()

# =========================================================================
# ÉTAPE 1 : SÉLECTION DE L'ODD ET DE L'INDICATEUR
# =========================================================================
st.subheader("1️⃣ Sélection de l'Indicateur Réglementaire THE 2027")

col_sdg, col_ind = st.columns([1, 2])

all_sdgs = framework.get_all_sdgs()
sdg_options = {f"ODD {k} - {v.get('short_name')}": int(k) for k, v in all_sdgs.items()}

with col_sdg:
    # Par défaut sur ODD 17 (obligatoire)
    selected_sdg_label = st.selectbox(
        "Objectif de Développement Durable (ODD) :",
        list(sdg_options.keys()),
        index=16  # ODD 17
    )
    chosen_sdg_num = sdg_options[selected_sdg_label]

# Liste des indicateurs pour cet ODD
indicators_list = framework.get_indicators_for_sdg(chosen_sdg_num)
indicator_dict = {f"{ind['indicator_id']} : {ind['name']}": ind for ind in indicators_list}

with col_ind:
    selected_ind_label = st.selectbox(
        "Indicateur spécifique :",
        list(indicator_dict.keys()),
        index=1 if len(indicator_dict) > 1 else 0
    )
    chosen_indicator = indicator_dict[selected_ind_label]

# Affichage des exigences officielles de l'indicateur sélectionné
ind_id = chosen_indicator.get("indicator_id")
ind_name = chosen_indicator.get("name")
ind_def = chosen_indicator.get("definition", ind_name)
ind_max_pts = chosen_indicator.get("max_points", 3.0)
is_policy_bonus = chosen_indicator.get("reviewed_policy_bonus", False) or "policy" in ind_id.lower()

st.info(
    f"📘 **Exigence THE 2027 pour [{ind_id}] :** {ind_def}\n\n"
    f"• **Type :** `{chosen_indicator.get('type', 'qualitative').upper()}` | "
    f"• **Points Max :** `{ind_max_pts} pts` | "
    f"• **Année Requise :** `2025`" + (" | • **Bonus Révision Politique (2022-2026) :** `+1.0 pt`" if is_policy_bonus else "")
)

st.write("")

# =========================================================================
# ÉTAPE 2 : SOUMISSION DE LA PREUVE (3 OPTIONS)
# =========================================================================
st.subheader("2️⃣ Soumission de la Preuve")

tab_text, tab_file, tab_url = st.tabs([
    "📝 Option A : Copier-Coller de Texte",
    "📎 Option B : Dépôt de Fichier (PDF, Word, Excel)",
    "🌐 Option C : URL Directe (Site UC3, Faculté, Facebook)"
])

extracted_content = ""
source_path_declared = ""
source_type_detected = "TEXTE"

with tab_text:
    pasted_text = st.text_area(
        "Collez ici le texte de la preuve (Français, Arabe ou Anglais) :",
        height=180,
        placeholder="Ex: Le Rectorat de l'Université Constantine 3 Salah Boubnider a signé le 10 février 2025 une convention..."
    )
    text_source_input = st.text_input("Source ou référence de ce texte :", value="https://univ-constantine3.dz/actualites/...")
    if pasted_text.strip():
        extracted_content = pasted_text.strip()
        source_path_declared = text_source_input.strip()
        source_type_detected = "TEXTE_MANUEL"

with tab_file:
    uploaded_file = st.file_uploader(
        "Uploadez un document institutionnel :",
        type=["pdf", "docx", "xlsx", "xls", "csv", "txt"],
        help="Le système extrait automatiquement le texte et les tableaux."
    )
    if uploaded_file is not None:
        # Enregistrement temporaire pour le parser
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        try:
            parse_res = doc_parser.parse_file(tmp_path)
            file_text = parse_res.get("full_text", "")
            st.success(f"✅ Fichier '{uploaded_file.name}' analysé avec succès ({len(file_text)} caractères extraits).")
            with st.expander("Aperçu du texte extrait du fichier :"):
                st.text(file_text[:800] + ("..." if len(file_text) > 800 else ""))
            
            extracted_content = file_text
            source_path_declared = uploaded_file.name
            source_type_detected = parse_res.get("source_type", "FICHIER")
        except Exception as e:
            st.error(f"Erreur d'extraction du fichier : {e}")

with tab_url:
    input_url = st.text_input(
        "Adresse URL publique (site officiel UC3, sous-domaine faculté ou page Facebook) :",
        placeholder="https://univ-constantine3.dz/... ou https://www.facebook.com/..."
    )
    col_crawl_btn, col_crawl_info = st.columns([1, 2])
    with col_crawl_btn:
        if st.button("Explorer et Récupérer l'URL"):
            if not input_url.strip():
                st.warning("Veuillez saisir une URL.")
            else:
                with st.spinner("Récupération en cours..."):
                    if "facebook.com" in input_url.lower():
                        st.info("ℹ️ URL Facebook détectée. Le collecteur institutionnel enregistre les métadonnées.")
                        extracted_content = f"Publication Facebook institutionnelle UC3 : {input_url}"
                        source_path_declared = input_url
                        source_type_detected = "FACEBOOK"
                    else:
                        crawl_res = web_crawler.fetch_page(input_url)
                        if crawl_res.get("status") == "success":
                            st.success(f"✅ Page récupérée : {crawl_res.get('title')}")
                            extracted_content = crawl_res.get("full_text", "")
                            source_path_declared = input_url
                            source_type_detected = "WEB_PAGE"
                            with st.expander("Aperçu du contenu web extrait :"):
                                st.write(extracted_content[:600] + "...")
                        else:
                            st.error(f"Impossible d'accéder à l'URL : {crawl_res.get('error_message')}")

# Entité UC3 concernée
entity_input = st.text_input(
    "Entité UC3 concernée (facultatif, auto-détectée si vide) :",
    value="Université Constantine 3 (Rectorat / Faculté)",
    help="Ex: Faculté de Médecine, Faculté Génie des Procédés, Institut des Techniques Urbaines..."
)

st.divider()

# =========================================================================
# ÉTAPE 3 : ÉVALUATION PAR LLM RÉEL (OU SIMULATEUR)
# =========================================================================
st.subheader("3️⃣ Lancement de l'Évaluation")

btn_eval = st.button("🚀 Évaluer la Preuve selon le Référentiel THE 2027", type="primary")

if btn_eval:
    if not extracted_content.strip():
        st.error("⚠️ Aucune preuve n'a été saisie. Veuillez coller du texte, uploader un fichier ou spécifier une URL valide.")
    else:
        with st.spinner("Analyse approfondie en cours par l'auditeur THE..."):
            evaluation_output = None
            used_real_llm = False

            # Tentative d'utilisation du LLM Réel si configuré
            if llm_evaluator.is_configured():
                llm_res = llm_evaluator.evaluate_evidence_with_llm(
                    indicator_id=ind_id,
                    indicator_name=ind_name,
                    indicator_definition=ind_def,
                    max_points=ind_max_pts,
                    evidence_text=extracted_content,
                    source_url_or_path=source_path_declared,
                    target_year=2025,
                    is_policy_bonus_eligible=is_policy_bonus
                )
                if "error" not in llm_res:
                    evaluation_output = llm_res
                    used_real_llm = True
                else:
                    st.warning(f"⚠️ Notification LLM : {llm_res.get('message')}. Bascule sur le simulateur analytique local.")

            # Fallback sur le simulateur d'évaluation THE 2027 si pas de LLM ou erreur
            if not evaluation_output:
                local_evaluator = THEEvidenceEvaluator(target_year=2025)
                local_res = local_evaluator.audit_evidence(
                    indicator_id=ind_id,
                    indicator_definition=ind_def,
                    evidence_text=extracted_content,
                    source_url_or_path=source_path_declared,
                    is_policy_indicator=is_policy_bonus
                )
                # Formattage conforme
                quote = extracted_content[:350] + ("..." if len(extracted_content) > 350 else "")
                
                status_cat = "Information vérifiée" if (local_res["quality"] == "specific" and local_res["is_public"]) else (
                    "Inférence" if local_res["quality"] == "general" else (
                        "Information à confirmer" if not local_res["is_public"] else "Absence de donnée"
                    )
                )

                evaluation_output = {
                    "information_found": extracted_content.split("\n")[0][:150],
                    "detected_year": local_res["detected_year"],
                    "justifying_quote": quote,
                    "uc3_entity": entity_input,
                    "quality": local_res["quality"],
                    "quality_justification": "Évalué selon l'adéquation des concepts clés, mentions institutionnelles et données chiffrées.",
                    "is_public": local_res["is_public"],
                    "is_self_contained": local_res["is_self_contained"],
                    "is_link_farm": local_res["is_link_farm"],
                    "confidence": "élevée" if local_res["quality"] == "specific" else "moyenne",
                    "status_category": status_cat,
                    "gap_or_alert": " | ".join(local_res["alerts"]) if local_res["alerts"] else "Aucune non-conformité majeure.",
                    "proposed_action": "publier" if not local_res["is_public"] else ("valider" if local_res["quality"] == "specific" else "compléter"),
                    "the_points_earned": local_res["total_points"],
                    "the_max_points": local_res["max_possible_points"],
                    "the_percentage": local_res["score_percentage"],
                    "recommendations": " | ".join(local_res["recommendations"]) if local_res["recommendations"] else "Preuve bien documentée.",
                    "engine_used": "Simulateur Analytique Local THE 2027"
                }

            # =========================================================================
            # ÉTAPE 4 : AFFICHAGE DE LA FICHE STRUCTURÉE CONFORME
            # =========================================================================
            st.markdown("---")
            engine_badge = "🤖 Évaluation par LLM Réel (Gemini)" if used_real_llm else "⚙️ Évaluation par Moteur Analytique Local"
            st.success(f"### 📋 Fiche d'Évaluation Structurée — {engine_badge}")

            # KPI CARDS
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Points THE", f"{evaluation_output['the_points_earned']} / {evaluation_output['the_max_points']} pts")
            k2.metric("Qualité de la Preuve", evaluation_output["quality"].upper())
            k3.metric("Caractère Public", "PUBLIQUE (+1 pt)" if evaluation_output["is_public"] else "NON PUBLIC (0 pt)")
            k4.metric("Catégorie de Fiabilité", evaluation_output["status_category"])

            # TABLEAU DÉTAILLÉ DE LA FICHE
            fiche_rows = [
                ("ODD et indicateur", f"{ind_id} - {ind_name}"),
                ("Exigence méthodologique THE", ind_def),
                ("Information trouvée", evaluation_output.get("information_found", "")),
                ("Année concernée (Priorité 2025)", str(evaluation_output.get("detected_year") or "Non spécifiée")),
                ("Source exacte", source_path_declared or "Texte fourni"),
                ("Extrait justificatif (verbatim)", evaluation_output.get("justifying_quote", "")),
                ("Entité UC3 concernée", evaluation_output.get("uc3_entity") or entity_input),
                ("Qualité de la preuve", f"{evaluation_output.get('quality', '').upper()} ({evaluation_output.get('quality_justification', '')})"),
                ("Publicité", "PUBLIQUE" if evaluation_output.get("is_public") else "INTERNE / PIÈCE JOINTE NON PUBLIQUE"),
                ("Niveau de confiance", evaluation_output.get("confidence", "").upper()),
                ("Lacune ou Alerte méthodologique", evaluation_output.get("gap_or_alert", "")),
                ("Action proposée", evaluation_output.get("proposed_action", "").upper()),
                ("Recommandation d'optimisation", evaluation_output.get("recommendations", ""))
            ]

            df_fiche = pd.DataFrame(fiche_rows, columns=["Champ Réglementaire", "Contenu / Décision"])
            st.table(df_fiche)

            # Alertes spécifiques
            alert_text = evaluation_output.get("gap_or_alert", "")
            if "ATTENTION" in alert_text or "REJET" in alert_text or "ANOMALIE" in alert_text or not evaluation_output.get("is_public"):
                st.warning(f"⚠️ **Alerte de Conformité THE 2027 :**\n{alert_text}")
            
            recom_text = evaluation_output.get("recommendations", "")
            if recom_text:
                st.info(f"💡 **Recommandation pour l'équipe UC3 :**\n{recom_text}")

            # =========================================================================
            # ÉTAPE 5 : EXPORT IMMÉDIAT EN EXCEL & WORD
            # =========================================================================
            st.markdown("#### 💾 Exporter cette Fiche d'Évaluation")

            export_fiche_obj = IndicatorFiche(
                odd_indicator=ind_id,
                indicator_title=ind_name,
                methodological_requirement=ind_def,
                information_found=evaluation_output.get("information_found", ""),
                year=evaluation_output.get("detected_year"),
                source_exact=source_path_declared,
                consultation_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                justifying_quote=evaluation_output.get("justifying_quote", ""),
                uc3_entity=evaluation_output.get("uc3_entity", entity_input),
                quality=evaluation_output.get("quality", "non_pertinente"),
                publicity="publique" if evaluation_output.get("is_public") else "interne",
                confidence=evaluation_output.get("confidence", "moyenne"),
                gap_or_alert=evaluation_output.get("gap_or_alert", ""),
                proposed_action=evaluation_output.get("proposed_action", "vérifier"),
                status_category=evaluation_output.get("status_category", "Information à confirmer"),
                the_points=evaluation_output.get("the_points_earned", 0.0),
                the_max_points=evaluation_output.get("the_max_points", 3.0),
                the_percentage=evaluation_output.get("the_percentage", 0.0)
            )

            exp_dir = ROOT_DIR / "exports"
            exp_dir.mkdir(exist_ok=True)
            
            clean_ind_filename = ind_id.replace(".", "_")
            out_excel = exp_dir / f"UC3_Evaluation_{clean_ind_filename}.xlsx"
            out_word = exp_dir / f"UC3_Evaluation_{clean_ind_filename}.docx"

            exporter.export_excel([export_fiche_obj.to_dict()], out_excel)
            exporter.export_word({
                "sdg_name": f"ODD {chosen_sdg_num}",
                "target_year": 2025,
                "total_indicators": 1,
                "total_points_earned": export_fiche_obj.the_points,
                "max_possible_points": export_fiche_obj.the_max_points,
                "sdg_completion_percentage": export_fiche_obj.the_percentage,
                "status_summary": {export_fiche_obj.status_category: 1},
                "fiches": [export_fiche_obj.to_dict()]
            }, out_word)

            ecol1, ecol2 = st.columns(2)
            with ecol1:
                with open(out_excel, "rb") as f_ex:
                    st.download_button(
                        label=f"📥 Télécharger la Fiche Excel ({out_excel.name})",
                        data=f_ex,
                        file_name=out_excel.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            with ecol2:
                with open(out_word, "rb") as f_wd:
                    st.download_button(
                        label=f"📥 Télécharger la Fiche Word ({out_word.name})",
                        data=f_wd,
                        file_name=out_word.name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
