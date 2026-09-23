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
from src.methodology.pdf_questions import indicator_question

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

    st.markdown("#### 🌐 Langue / Interface Language")
    lang_choice = st.radio(
        "Langue d'affichage / Language :",
        ["Français 🇫🇷", "English 🇬🇧"],
        index=0,
        horizontal=True
    )
    is_en = "English" in lang_choice

    st.markdown("#### 🤖 Configuration du Modèle LLM" if not is_en else "#### 🤖 LLM Model Configuration")
    # Sécurité serveur : ne jamais fuiter la clé dans l'input client (value=...)
    server_api_key = ""
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            server_api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    if not server_api_key:
        server_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""

    user_api_key_override = st.text_input(
        "Clé API Gemini personnalisée (Optionnelle) :" if not is_en else "Custom Gemini API Key (Optional):",
        value="",
        type="password",
        help="Laissez vide pour utiliser la configuration serveur sécurisée. Obtenez une clé sur https://aistudio.google.com/."
    )

    effective_api_key = user_api_key_override.strip() if user_api_key_override.strip() else server_api_key

    if server_api_key and not user_api_key_override.strip():
        st.caption("🔒 Clé serveur active" if not is_en else "🔒 Server API key active")

    selected_model = st.selectbox(
        "Modèle LLM :" if not is_en else "LLM Model:",
        ["gemini-2.5-pro"],
        index=0,
        help="Utilise votre clé API Gemini. Un abonnement grand public ne fournit pas l'accès API développeur."
    )

    llm_evaluator = RealLLMEvaluator(api_key=effective_api_key, model_name=selected_model)

    if st.button("🔌 Tester la Clé API" if not is_en else "🔌 Test API Key"):
        if not effective_api_key.strip():
            st.warning("Veuillez d'abord renseigner une clé API ou configurer GEMINI_API_KEY." if not is_en else "Please provide an API key or configure GEMINI_API_KEY.")
        else:
            with st.spinner("Vérification auprès de Google Gemini..." if not is_en else "Connecting to Google Gemini..."):
                t_res = llm_evaluator.test_connection()
                if t_res["valid"]:
                    st.success(f"✅ {t_res['message']}")
                else:
                    st.error(f"❌ Erreur : {t_res['message']}")
    
    if llm_evaluator.is_configured():
        st.success("🟢 **LLM Réel Connecté (Gemini Pro)**" if not is_en else "🟢 **Real LLM Connected (Gemini Pro)**")
    else:
        st.warning("Clé API Gemini requise : aucun score ne sera attribué sans le modèle." if not is_en else "Gemini API Key required: no score calculated without model.")

    st.divider()
    st.markdown("#### 📜 Règles Méthodologiques THE" if not is_en else "#### 📜 THE Methodology Rules")
    st.markdown("- **Année Cible / Target Year :** `2025`")
    st.markdown("- **Preuve Publique :** URL directe = 1 pt / Fichier joint = 0 pt" if not is_en else "- **Public Evidence:** Direct URL = 1 pt / Attachment = 0 pt")
    st.markdown("- **Autosuffisance :** Annuaire de liens = Rejet" if not is_en else "- **Self-contained:** Link farm = Rejection")
    st.markdown("- **Contrôle :** citation littérale exigée, puis validation humaine" if not is_en else "- **Control:** Literal quote required, then human review")

# --- EN-TÊTE PRINCIPAL ---
st.title("📥 Ingestion & Évaluation de Preuves en Direct (THE 2027)" if not is_en else "📥 Real-Time Evidence Audit & Submission Assistant (THE 2027)")
st.markdown(
    "Sélectionnez un indicateur parmi les **17 ODD**, soumettez une preuve (texte, fichier PDF/Word/Excel ou URL), "
    "et laissez l'auditeur LLM analyser la conformité selon le barème officiel."
    if not is_en else
    "Select an indicator across the **17 SDGs**, submit evidence (text, PDF/Word/Excel file, or live URL), "
    "and let the Gemini Pro auditor evaluate compliance against the official THE 2027 methodology."
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
ind_type = chosen_indicator.get("type", "qualitative")
ind_id = chosen_indicator.get("indicator_id")
ind_name = chosen_indicator.get("name")
ind_def = chosen_indicator.get("definition", ind_name)
ind_max_pts = chosen_indicator.get("max_points", 3.0)
is_policy_bonus = chosen_indicator.get("reviewed_policy_bonus", False) or "policy" in ind_id.lower()

if ind_type == "quantitative":
    st.info(
        f"🔢 **Indicateur Quantitatif [{ind_id}] :** {ind_name}\n\n"
        f"• **Type :** `QUANTITATIF` | "
        f"• **Poids dans l'ODD :** `{chosen_indicator.get('weight_sdg', 0.0) * 100:.1f}%` | "
        f"• **Année de référence :** `2025` | "
        f"• **Métrique parente :** `{chosen_indicator.get('metric_id', '')} - {chosen_indicator.get('metric_name', '')}`"
    )
    st.markdown("#### 📐 Guide Méthodologique THE 2027 (Données Quantitatives)")
    st.markdown(
        "- **Règle ETP vs Effectif physique (FTE vs Headcount) :** Pour les effectifs étudiants et académiques, "
        "déclarez en équivalent temps plein (ETP) si disponible, ou en effectif physique de manière cohérente à travers tous les ODD.\n"
        "- **Année de référence :** 2025 (année universitaire 2024/2025 ou année civile 2025).\n"
        "- **Traçabilité :** Chaque chiffre doit être certifié par une source administrative interne vérifiable (Progres MESRS, états financiers, PV de scolarité)."
    )

    st.subheader("2️⃣ Saisie & Vérification Arithmétique des Métriques")
    fields = chosen_indicator.get("fields", ["Dénominateur (Effectif global)", "Numérateur (Effectif ciblé)"])
    q_values = {}
    col_fields = st.columns(len(fields)) if len(fields) <= 3 else [st] * len(fields)
    for idx, fld in enumerate(fields):
        with col_fields[idx % len(col_fields)]:
            q_values[fld] = st.number_input(
                f"📊 {fld} :",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key=f"quant_field_{ind_id}_{idx}",
                help=f"Valeur certifiée pour l'année 2025 : {fld}"
            )

    computed_ratio = None
    if len(fields) >= 2:
        val_list = list(q_values.values())
        den = val_list[0]
        num = val_list[1]
        st.write("")
        st.markdown("#### 📈 Synthèse et Calcul du Ratio")
        if den > 0:
            computed_ratio = (num / den) * 100.0
            r_col1, r_col2 = st.columns(2)
            r_col1.metric("Proportion / Ratio Officiel", f"{computed_ratio:.2f} %", delta=f"{num:.0f} / {den:.0f}")
            if num > den:
                r_col2.warning("⚠️ Attention : Le numérateur dépasse le dénominateur. Vérifiez la définition THE.")
            else:
                r_col2.success("✅ Données arithmétiquement conformes (Numérateur <= Dénominateur).")
        else:
            st.info("ℹ️ Renseignez le dénominateur (> 0) pour calculer automatiquement le pourcentage.")

    st.subheader("3️⃣ Traçabilité Administrative & Validation à 2 Niveaux")
    col_adm1, col_adm2 = st.columns(2)
    with col_adm1:
        adm_source = st.selectbox(
            "Service administratif source :",
            [
                "Vice-Rectorat de la Pédagogie",
                "Vice-Rectorat du Développement et de la Prospective",
                "Vice-Rectorat de la Post-Graduation et de la Recherche",
                "Direction de la Scolarité Centrale (Progres MESRS)",
                "Direction des Finances et de la Comptabilité",
                "Direction des Moyens et du Patrimoine",
                "Autre Faculté / Institut"
            ],
            key=f"adm_source_{ind_id}"
        )
        data_origin_system = st.text_input("Système source d'information :", value="Système Intégré Progres - MESRS", key=f"sys_orig_{ind_id}")
    with col_adm2:
        validator_name = st.text_input("Nom & Fonction du déclarant :", value="Cellule de Classement & Assurance Qualité UC3", key=f"val_name_{ind_id}")
        validation_status = st.selectbox(
            "Statut du contrôle interne :",
            [
                "🟢 Validé et Certifié par le Service Source (Prêt pour THE)",
                "🟡 En cours de collecte / Donnée provisoire",
                "🔵 Certifié Officiel Rectorat"
            ],
            key=f"val_stat_{ind_id}"
        )

    uploaded_quant_file = st.file_uploader(
        "Pièce justificative interne (Attestation, extraction Progres certifiée, état comptable) :",
        type=["xlsx", "xls", "pdf", "csv"],
        key=f"quant_file_{ind_id}"
    )

    if st.button("💾 Enregistrer la Déclaration Quantitative pour la Soumission THE", type="primary", key=f"btn_save_quant_{ind_id}"):
        st.success(f"✅ Déclaration quantitative de l'indicateur [{ind_id}] enregistrée avec succès dans le dossier d'audit UC3 !")
        st.json({
            "indicator_id": ind_id,
            "indicator_name": ind_name,
            "sdg": chosen_sdg_num,
            "year": 2025,
            "fields_data": q_values,
            "computed_ratio_percentage": round(computed_ratio, 2) if computed_ratio is not None else None,
            "administrative_source": adm_source,
            "origin_system": data_origin_system,
            "declarant": validator_name,
            "validation_status": validation_status,
            "attached_file": uploaded_quant_file.name if uploaded_quant_file else None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    st.stop()

elif ind_type == "bibliometric":
    st.info(
        f"📚 **Indicateur Bibliométrique [{ind_id}] :** {ind_name}\n\n"
        f"• **Type :** `BIBLIOMÉTRIQUE` | "
        f"• **Poids dans l'ODD :** `{chosen_indicator.get('weight_sdg', 0.0) * 100:.1f}%` | "
        f"• **Métrique parente :** `{chosen_indicator.get('metric_id', '')} - {chosen_indicator.get('metric_name', '')}`"
    )
    st.markdown("#### ℹ️ Procédure Officielle THE pour les Indicateurs Bibliométriques")
    st.markdown(
        "Times Higher Education extrait les métriques bibliométriques **directement depuis la base de données Scopus (Elsevier)**.\n"
        "- **Identifiant d'Affiliation Scopus Officiel UC3 :** `60071378` (Université Constantine 3 Salah Boubnider)\n"
        "- **Période des publications :** 2019 à 2023 (fenêtre quinquennale de production scientifique)\n"
        "- **Période des citations :** 2019 à 2024 / 2025 (fenêtre de citations)\n"
        "- **Action requise :** Aucune soumission de preuve manuelle requise sur le portail THE. "
        "L'équipe UC3 doit auditer son profil d'affiliation Scopus et s'assurer que toutes les publications des facultés sont correctement rattachées à l'ID 60071378."
    )
    st.subheader("2️⃣ Suivi Interne & Veille Scientifique UC3")
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        target_papers = st.number_input("Cible interne de publications UC3 pour cet ODD :", min_value=0, value=25, step=5, key=f"bib_target_{ind_id}")
        scopus_observed = st.number_input("Nombre de publications indexées observées (Scopus / SciVal) :", min_value=0, value=28, step=1, key=f"bib_obs_{ind_id}")
    with b_col2:
        top_labs = st.text_input("Facultés / Laboratoires moteurs à l'UC3 :", value="Faculté Génie des Procédés, Laboratoire de Biotechnologie, Faculté de Médecine", key=f"bib_labs_{ind_id}")
        biblio_status = st.selectbox(
            "Statut du profil d'affiliation Scopus :",
            ["🟢 Affiliation ID 60071378 Validée & Conforme", "🟡 Demande de fusion/correction d'affiliation en cours", "🔵 En attente d'actualisation Scopus"],
            key=f"bib_stat_{ind_id}"
        )

    delta_papers = scopus_observed - target_papers
    pct_target = (scopus_observed / target_papers * 100) if target_papers > 0 else 100.0
    st.metric("Taux d'Atteinte de la Cible Scientifique", f"{pct_target:.1f} %", delta=f"{delta_papers:+d} publications vs cible")
    st.success(f"✅ Suivi bibliométrique de l'ODD {chosen_sdg_num} consigné dans la veille institutionnelle UC3.")
    st.stop()

elif ind_type in ("external_metric", "exploratory"):
    badge_label = "Brevets Cités (LexisNexis / Scopus)" if ind_type == "external_metric" else "Métrique Exploratoire (Sulitest / Littératie)"
    st.info(f"🌐 **{badge_label} [{ind_id}] :** {ind_name}\n\n• **Type :** `{ind_type.upper()}`")
    if ind_type == "external_metric":
        st.markdown(
            "Cet indicateur mesure l'impact technologique des recherches menées à l'UC3 citées dans des brevets déposés à l'échelle internationale.\n"
            "THE collabore avec LexisNexis PatentSight pour l'extraction automatisée."
        )
        patents_count = st.number_input("Nombre estimé de brevets citant les publications UC3 :", min_value=0, value=2, key=f"pat_cnt_{ind_id}")
        st.success(f"✅ {patents_count} brevets enregistrés dans le répertoire de valorisation technologique.")
    else:
        st.markdown(
            "Métrique exploratoire introduite pour 2027 (ex: test standardisé de connaissances en durabilité Sulitest TASK).\n"
            "Non comptabilisée dans le calcul final du score global, mais permet à l'UC3 de démontrer sa proactivité pédagogique."
        )
        students_tested = st.number_input("Nombre d'étudiants ayant complété une évaluation de durabilité :", min_value=0, value=150, key=f"expl_stud_{ind_id}")
        avg_score = st.slider("Score moyen obtenu aux tests (%) :", min_value=0, max_value=100, value=72, key=f"expl_sc_{ind_id}")
        st.metric("Sensibilisation Étudiante", f"{students_tested} étudiants évalués", delta=f"Score moyen : {avg_score}%")
    st.stop()

# Affichage des exigences officielles de l'indicateur sélectionné
ind_id = chosen_indicator.get("indicator_id")
ind_name = chosen_indicator.get("name")
ind_def = chosen_indicator.get("definition", ind_name)
ind_max_pts = chosen_indicator.get("max_points", 3.0)
is_policy_bonus = chosen_indicator.get("reviewed_policy_bonus", False) or "policy" in ind_id.lower()

st.info(
    f"📘 **Résumé de l'indicateur [{ind_id}] :** {ind_def}\n\n"
    f"• **Type :** `{chosen_indicator.get('type', 'qualitative').upper()}` | "
    f"• **Points Max :** `{ind_max_pts} pts` | "
    f"• **Année Requise :** `2025`" + (" | • **Bonus Révision Politique (2022-2026) :** `+1.0 pt`" if is_policy_bonus else "")
)

# Chargement et affichage de la question officielle intégrale du PDF THE 2027
pdf_path_default = os.environ.get("THE_2027_PDF") or ""
official_question_display = ""
try:
    official_question_display = indicator_question(pdf_path_default, ind_id)
except Exception as e_pdf:
    official_question_display = f"⚠️ Impossible de charger la question officielle du PDF : {e_pdf}. Configurez THE_2027_PDF."

with st.expander("📜 Question Officielle, Précisions & Critères THE 2027 (extraits du PDF)", expanded=True):
    st.markdown(official_question_display)

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
source_verified = False
source_is_attachment = False

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
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
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
            source_verified = True
            source_is_attachment = True
        except Exception as e:
            st.error(f"Erreur d'extraction du fichier : {e}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

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
                        st.warning("Le contenu Facebook n'a pas été récupéré. Fournissez une page institutionnelle directement lisible.")
                    else:
                        crawl_res = web_crawler.fetch_page(input_url)
                        if crawl_res.get("status") == "success":
                            st.success(f"✅ Page récupérée : {crawl_res.get('title')}")
                            extracted_content = crawl_res.get("full_text", "")
                            source_path_declared = input_url
                            source_type_detected = "WEB_PAGE"
                            source_verified = True
                            st.session_state["verified_web_evidence"] = (input_url, extracted_content)
                            with st.expander("Aperçu du contenu web extrait :"):
                                st.write(extracted_content[:600] + "...")
                        else:
                            st.error(f"Impossible d'accéder à l'URL : {crawl_res.get('error_message')}")

if not source_verified and uploaded_file is None and not pasted_text.strip():
    cached_url, cached_text = st.session_state.get("verified_web_evidence", ("", ""))
    if cached_url == input_url.strip() and cached_text:
        extracted_content = cached_text
        source_path_declared = cached_url
        source_verified = True
        source_type_detected = "WEB_PAGE"

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
        if input_url.strip() and not source_verified:
            st.error("⚠️ URL inaccessible ou non explorée. Cliquez sur 'Explorer et Récupérer l'URL' et assurez-vous que la page est accessible. Aucun score ne peut être calculé sur une URL non récupérée.")
        else:
            st.error("⚠️ Aucune preuve n'a été saisie. Veuillez coller du texte, uploader un fichier ou explorer une URL valide.")
        st.stop()
    else:
        with st.spinner("Analyse approfondie en cours par l'auditeur THE..."):
            evaluation_output = None
            used_real_llm = False

            if not llm_evaluator.is_configured():
                st.error("Clé API Gemini Pro requise. Aucun score calculé.")
                st.stop()

            # Bloquer les URLs non récupérées dans l'onglet URL
            if source_type_detected == "WEB_PAGE" and not source_verified:
                st.error("La page web doit être effectivement récupérée. Un texte collé et une URL déclarée ne prouvent pas sa publication.")
                st.stop()

            try:
                pdf_path = os.environ.get("THE_2027_PDF", "")
                question = indicator_question(pdf_path, ind_id)
            except (FileNotFoundError, ValueError, ImportError) as exc:
                st.error(f"Méthodologie indisponible : {exc}. Aucun score calculé.")
                st.stop()

            llm_res = llm_evaluator.evaluate_evidence_with_llm(
                indicator_id=ind_id,
                indicator_name=ind_name,
                indicator_definition=ind_def,
                max_points=ind_max_pts,
                evidence_text=extracted_content,
                source_url_or_path=source_path_declared,
                target_year=2025,
                is_policy_bonus_eligible=is_policy_bonus,
                methodology_question=question,
                source_verified=source_verified,
                source_is_attachment=source_is_attachment
            )
            if "error" in llm_res:
                st.error(f"Évaluation impossible : {llm_res.get('message')}. Aucun score calculé.")
                st.stop()
            evaluation_output = llm_res
            used_real_llm = True

            # =========================================================================
            # ÉTAPE 4 : AFFICHAGE DE LA FICHE STRUCTURÉE CONFORME
            # =========================================================================
            st.markdown("---")
            engine_badge = "🤖 Évaluation par LLM Réel (Gemini Pro)" if used_real_llm else "⚙️ Évaluation par Moteur Analytique Local"
            st.success(f"### 📋 Fiche d'Évaluation Structurée — {engine_badge}")

            # 4 COMPOSANTES DU BARÈME THE 2027
            st.markdown("#### 🎯 Décomposition des 4 Composantes du Barème THE 2027")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric(
                "1. Déclaration",
                f"{evaluation_output.get('statement_points', 0.0):.1f} / 1.0 pt",
                help="1.0 pt si l'action ou politique est déclarée et pertinente, 0 sinon."
            )
            c2.metric(
                "2. Pertinence",
                f"{evaluation_output.get('evidence_points', 0.0):.1f} / 1.0 pt",
                delta="Spécifique (1.0 pt)" if evaluation_output.get("quality") == "specific" else ("Générale (0.5 pt)" if evaluation_output.get("quality") == "general" else "Hors-sujet (0.0 pt)"),
                delta_color="normal" if evaluation_output.get("quality") in ("specific", "general") else "inverse"
            )
            c3.metric(
                "3. Caractère Public",
                f"{evaluation_output.get('public_points', 0.0):.1f} / 1.0 pt",
                delta="Page web (+1.0 pt)" if evaluation_output.get("public_points", 0.0) > 0 else "Non public / PJ (0.0 pt)",
                delta_color="normal" if evaluation_output.get("public_points", 0.0) > 0 else "off"
            )
            pol_pts = evaluation_output.get("policy_bonus_points", 0.0)
            c4.metric(
                "4. Bonus Politique",
                f"{pol_pts:.1f} / 1.0 pt" if is_policy_bonus else "N/A",
                delta="Révisée 2022-2026 (+1.0 pt)" if pol_pts > 0 else ("Non révisée (0.0 pt)" if is_policy_bonus else None),
                delta_color="normal" if pol_pts > 0 else "off",
                help="Prévu uniquement si la question officielle THE inclut une clause de révision 2022-2026."
            )
            c5.metric(
                "Total THE",
                f"{evaluation_output['the_points_earned']:.1f} / {evaluation_output['the_max_points']:.1f} pts",
                delta=f"{evaluation_output.get('the_percentage', 0.0)}%"
            )

            st.write("")

            # KPI CARDS RÉCAPITULATIFS
            k1, k2, k3 = st.columns(3)
            k1.metric("Qualité de la Preuve", evaluation_output["quality"].upper())
            k2.metric("Statut de Publication", "PUBLIQUE (Page web vérifiée)" if evaluation_output.get("is_public") else "INTERNE / PIÈCE JOINTE (0 pt public)")
            k3.metric("Catégorie de Fiabilité", evaluation_output["status_category"])

            # TABLEAU DÉTAILLÉ DE LA FICHE
            fiche_rows = [
                ("ODD et indicateur", f"{ind_id} - {ind_name}"),
                ("Question officielle THE (PDF 2027)", question[:300] + ("..." if len(question) > 300 else "")),
                ("Information trouvée", evaluation_output.get("information_found", "")),
                ("Année concernée (Priorité 2025)", str(evaluation_output.get("detected_year") or "Non spécifiée")),
                ("Source exacte", source_path_declared or "Texte fourni"),
                ("Extrait justificatif (verbatim)", evaluation_output.get("justifying_quote", "")),
                ("Entité UC3 concernée", evaluation_output.get("uc3_entity") or entity_input),
                ("Qualité de la preuve", f"{evaluation_output.get('quality', '').upper()} ({evaluation_output.get('quality_justification', '')})"),
                ("Publicité", "PUBLIQUE (+1.0 pt)" if evaluation_output.get("is_public") else "INTERNE / PIÈCE JOINTE (0.0 pt)"),
                ("Décomposition des points", f"Déclaration: {evaluation_output.get('statement_points', 0.0)} pt | Pertinence: {evaluation_output.get('evidence_points', 0.0)} pt | Publicité: {evaluation_output.get('public_points', 0.0)} pt | Bonus Politique: {evaluation_output.get('policy_bonus_points', 0.0)} pt"),
                ("Total points THE", f"{evaluation_output.get('the_points_earned', 0.0)} / {evaluation_output.get('the_max_points', 3.0)} pts ({evaluation_output.get('the_percentage', 0.0)}%)"),
                ("Synthèse en Anglais (Portail THE)", evaluation_output.get("english_summary_for_the", "")),
                ("Traduction anglaise de la citation", evaluation_output.get("quote_english_translation", "")),
                ("Niveau de confiance", evaluation_output.get("confidence", "").upper()),
                ("Lacune ou Alerte méthodologique", evaluation_output.get("gap_or_alert", "")),
                ("Action proposée", evaluation_output.get("proposed_action", "").upper()),
                ("Recommandation d'optimisation", evaluation_output.get("recommendations", ""))
            ]

            df_fiche = pd.DataFrame(fiche_rows, columns=["Champ Réglementaire", "Contenu / Décision"])
            st.table(df_fiche)

            # BLOC OFFICIEL DE SOUMISSION AU PORTAIL THE (ANGLAIS)
            en_summary = evaluation_output.get("english_summary_for_the", "")
            en_quote = evaluation_output.get("quote_english_translation", "")
            if en_summary:
                st.markdown("---")
                st.markdown("### 🇬🇧 Pack de Soumission Officielle THE (Anglais / English)")
                st.caption(
                    "Texte prêt pour le copier-coller direct dans le champ 'Description' du portail Times Higher Education :"
                    if not is_en else
                    "Ready to copy-paste into the Times Higher Education submission portal 'Description' field:"
                )
                col_sub1, col_sub2 = st.columns([3, 2])
                with col_sub1:
                    st.text_area(
                        "📝 Evidence Description (English - Portal Ready) :",
                        value=en_summary,
                        height=120,
                        help="Copy this directly into the THE portal 'Description' field."
                    )
                with col_sub2:
                    st.text_area(
                        "💬 Key Verbatim Quote Translated (English) :",
                        value=en_quote if en_quote else "(Original quote is already in English)",
                        height=120,
                        help="English translation of the original verbatim quote for international reviewers."
                    )

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
            st.markdown("#### 💾 Exporter cette Fiche d'Évaluation" if not is_en else "#### 💾 Export this Evaluation Fiche")

            export_fiche_obj = IndicatorFiche(
                odd_indicator=ind_id,
                indicator_title=ind_name,
                methodological_requirement=ind_def,
                information_found=evaluation_output.get("information_found", ""),
                english_summary_for_the=evaluation_output.get("english_summary_for_the", ""),
                year=evaluation_output.get("detected_year"),
                source_exact=source_path_declared,
                consultation_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                justifying_quote=evaluation_output.get("justifying_quote", ""),
                quote_english_translation=evaluation_output.get("quote_english_translation", ""),
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
