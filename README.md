# Assistant Institutionnel RAG - THE Sustainability Impact Ratings 2027
### Université Constantine 3 Salah Boubnider (UC3)

Plateforme d'intelligence artificielle et d'extraction RAG développée spécifiquement pour la collecte, l'évaluation et la validation des indicateurs de durabilité de l'**Université Constantine 3 (UC3)** selon le référentiel méthodologique officiel **Times Higher Education (THE) Sustainability Impact Ratings 2027 (v1.0)**.

---

## 🎯 Périmètre et Fonctionnalités

Le système implémente l'ensemble des **5 fonctions clés** définies pour l'UC3 :

1. **Référentiel Méthodologique Numérisé (THE 2027)**
   - Modélisation exhaustive des **17 ODD**, métriques, indicateurs et définitions.
   - Intégration stricte de l'année cible (**2025**).
   - Règles de calcul du score Overall (ODD 17 obligatoire pour 22% + Top 3 ODD pour 26% chacun = 100%).

2. **Collecte Intelligente Multi-source**
   - Sites web officiels de l'UC3 et des facultés (`*.univ-constantine3.dz`).
   - Documents administratifs internes (PDF, Word `.docx`, Excel `.xlsx`, CSV).
   - Publications Facebook institutionnelles publiques des pages autorisées.
   - Moteur OCR multilingue (Français, Arabe, Anglais) pour arrêtés et conventions scannées.

3. **Moteur d'Extraction RAG Zéro-Hallucination**
   - Interdiction stricte de supposer ou d'inventer une valeur absente.
   - Distinction formelle entre les 4 catégories :
     * 🟢 **Information vérifiée**
     * 🔵 **Inférence**
     * 🟡 **Information à confirmer**
     * 🔴 **Absence de donnée**
   - Détection des contradictions temporelles ou quantitatives multi-sources.
   - Préservation de la citation textuelle verbatim et de la date de consultation.

4. **Simulateur d'Évaluation des Preuves (THE LLM Evaluator)**
   - Notation de la preuve : **Spécifique (1.0 pt)**, **Générale (0.5 pt)**, **Non pertinente (0 pt)**.
   - Statut de publicité : **Publique (1.0 pt)** vs **Interne / Pièce jointe (0.0 pt)**.
     *(Alerte THE 2027 : tout document attaché est automatiquement noté non public s'il n'est pas hébergé sur le web).*
   - **Contrôle d'autosuffisance ("Self-contained")** : Rejet automatique des annuaires de liens (*link farms*).
   - Recommandation de migration des posts Facebook en pages web officielles durables.

5. **Tableau de Bord Institutionnel & Validation Humaine**
   - Vue globale des 17 ODD avec simulation du score THE.
   - Pilote opérationnel approfondi sur l'**ODD 17 (Partenariats)**.
   - Espace de validation humaine pour les ambassadeurs ODD et le Rectorat.
   - Génération en un clic des dossiers d'export **Excel (.xlsx)** et **Word (.docx)**.

---

## 🏗️ Structure du Projet

```
splendid-lavoisier/
├── data/
│   ├── the_2027_taxonomy.json          # Référentiel complet des 17 ODD THE 2027
│   └── uc3_samples/
│       └── sample_data_loader.py       # Corpus représentatif UC3 (Web, Doc, FB)
├── exports/                            # Dossiers d'export générés (Excel, Word)
├── src/
│   ├── methodology/
│   │   └── the_2027_framework.py       # Moteur du référentiel et calculs THE
│   ├── evaluation/
│   │   └── the_evaluator.py            # Simulateur de validation THE LLM
│   ├── ingestion/
│   │   ├── doc_parser.py               # Extracteur PDF, DOCX, XLSX, CSV
│   │   ├── web_crawler.py              # Crawleur web UC3
│   │   ├── facebook_collector.py       # Collecteur Facebook institutionnel
│   │   └── ocr_engine.py               # OCR multilingue (FR, AR, EN)
│   ├── rag/
│   │   ├── models.py                   # Schéma de la fiche structurée
│   │   ├── retriever.py                # Recherche hybride et sémantique
│   │   └── extractor.py                # Moteur d'extraction zéro-hallucination
│   ├── pilot/
│   │   └── sdg17_pilot.py              # Orchestration du pilote ODD 17
│   ├── export/
│   │   └── exporter.py                 # Exporteur Word & Excel
│   └── dashboard/
│       └── app.py                      # Application Web Streamlit
├── tests/                              # Suite de tests automatisés (pytest)
│   ├── test_taxonomy.py
│   ├── test_evaluator.py
│   ├── test_extractor.py
│   └── test_pilot_and_export.py
└── run_pipeline.py                     # Script CLI principal
```

---

## 🚀 Guide de Démarrage

### Évaluation réelle avec Gemini Pro

Le parcours principal évalue une seule **preuve qualitative** à la fois. Installez les dépendances avec `python -m pip install -r requirements.txt`, puis configurez `GEMINI_API_KEY` et `THE_2027_PDF` (chemin absolu du document officiel *Sustainability Impact Ratings Methodology 2027 v1.0*). Sous PowerShell :

```powershell
$env:GEMINI_API_KEY = "votre-cle-api"
$env:THE_2027_PDF = "C:\\chemin\\vers\\THE.SustainabilityImpactRatings.METHODOLOGY.2027.v1.0.pdf"
python run_pipeline.py
```

Ne commitez jamais la clé ni le PDF méthodologique. Le modèle par défaut est `gemini-3.6-flash`, accessible au niveau sans frais sous réserve des quotas et des autorisations du projet. `gemini-3.1-pro-preview` reste proposé pour les projets avec facturation API. Les modèles 2.5 ne sont plus proposés aux nouveaux utilisateurs. Après une mise à jour, redémarrez Streamlit et testez la connexion avec la même clé. L'abonnement grand public à Gemini Pro et la facturation de l'API Gemini sont distincts : vérifiez l'accès API associé à votre clé. Sans clé, PDF, page effectivement récupérée ou citation exacte, le tableau de bord ne produit aucun score. Une pièce jointe analysable est évaluée comme non publique. Le score reste une **estimation interne**, soumise à validation humaine, et non une décision officielle de THE.

`--pilot` et `--export` exécutent encore un ancien corpus fictif de démonstration ; leurs chiffres et rapports ne constituent pas une collecte UC3 vérifiée et ne doivent pas être soumis.

### 1. Prérequis
- Python 3.10+
- Dépendances installées : `streamlit`, `pandas`, `openpyxl`, `python-docx`, `pypdf`, `beautifulsoup4`, `pytest`.

### 2. Exécution du Pilote et Génération des Rapports
Pour lancer l'audit complet sur l'ODD 17 et générer les exports officiels :
```bash
python run_pipeline.py
```

### 3. Lancement du Tableau de Bord Interactif
Pour ouvrir l'interface utilisateur institutionnelle :
```bash
python run_pipeline.py --dashboard
# ou directement :
python -m streamlit run src/dashboard/app.py
```
Le tableau de bord sera accessible à l'adresse : `http://localhost:8501`.

### 4. Exécution de la Suite de Tests
```bash
python -m pytest tests -v
```
Tous les tests valident l'intégrité de la taxonomie des 17 ODD, le rejet des link-farms, la pénalité des documents attachés non publics, et la règle d'or zéro-hallucination.
