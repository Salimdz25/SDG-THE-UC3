"""
Chargeur de Données de Démonstration & Corpus Réel pour l'Université Constantine 3
Fournit des exemples réels et institutionnels couvrant :
- Sites Web officiels UC3
- Documents administratifs internes (Conventions, Arrêtés, Rapports)
- Publications Facebook officielles
- Données avec anomalies (pièges de liens, dates antérieures, documents non publiés)
"""

from typing import List, Dict, Any

UC3_SAMPLE_DOCUMENTS = [
    {
        "title": "Colloque International sur la Transition Énergétique et l'Économie Circulaire 2025",
        "url_or_path": "https://univ-constantine3.dz/colloque-odd-transition-energetique-2025/",
        "source_type": "WEB_PAGE",
        "entity": "Rectorat & Faculté Génie des Procédés UC3",
        "date": "2025-05-18",
        "is_public": True,
        "text": """Université Constantine 3 Salah Boubnider - 18 mai 2025.
Le Rectorat de l'Université Constantine 3, en partenariat avec la Faculté de Génie des Procédés, a réuni plus de 180 participants lors du Colloque International sur le Dialogue Intersectoriel pour les ODD et la Transition Énergétique. 
L'événement a rassemblé des représentants du Ministère de l'Enseignement Supérieur, de l'Agence Nationale des Déchets (AND), de Sonelgaz, ainsi que des associations de protection de l'environnement de la Wilaya de Constantine. 
Les débats ont porté sur les mécanismes concrets de décarbonation des campus et le recyclage des eaux industrielles.
Un comité mixte UC3-Industrie a été officiellement mis en place à l'issue de ces journées."""
    },
    {
        "title": "Convention-cadre UC3 et Direction de l'Environnement de Constantine",
        "url_or_path": "C:/Archives_Rectorat/Conventions_2025/Convention_Environnement_Wilaya_Constantine_2025.pdf",
        "source_type": "PDF_INTERNE",
        "entity": "Rectorat UC3",
        "date": "2025-02-10",
        "is_public": False,
        "text": """RÉPUBLIQUE ALGÉRIENNE DÉMOCRATIQUE ET POPULAIRE
Université Constantine 3 Salah Boubnider
Convention de Coopération Institutionnelle relative aux Politiques de Développement Durable (ODD).
Signée le 10 février 2025 entre le Recteur de l'Université Constantine 3 et la Direction de l'Environnement de la Wilaya de Constantine.
Objet : Implication directe des experts et enseignants-chercheurs de l'UC3 dans l'élaboration, le suivi et l'évaluation du Plan Climat et de la politique de gestion des déchets de la région de Constantine.
L'UC3 fournira une assistance technique et des modèles de prospective environnementale."""
    },
    {
        "title": "Publication Facebook - Campagne de Bénévolat et Reboisement du Campus",
        "url_or_path": "https://www.facebook.com/univconstantine3.officiel/posts/pfbid025983726482",
        "source_type": "FACEBOOK",
        "entity": "Faculté d'Architecture et Clubs Scientifiques UC3",
        "date": "2025-03-21",
        "is_public": True,
        "text": """Université Salah Boubnider Constantine 3 - Page Officielle.
Grande journée de volontariat et d'action environnementale sur le campus d'Ali Mendjeli ! 
En ce 21 mars 2025, plus de 300 étudiants de l'UC3, en collaboration avec l'association écologique 'Nass El Khir Constantine' et le Croissant Rouge Algérien, ont mené une vaste opération de reboisement et de tri sélectif des déchets plastiques. 
Des ateliers pratiques de sensibilisation aux Objectifs de Développement Durable (ODD) ont été animés au profit des résidents universitaires et des riverains."""
    },
    {
        "title": "Offre de Formation - Masters Spécialisés en Durabilité UC3",
        "url_or_path": "https://fac-gp.univ-constantine3.dz/formations/master-genie-environnement-2025/",
        "source_type": "WEB_PAGE",
        "entity": "Faculté Génie des Procédés",
        "date": "2025-09-10",
        "is_public": True,
        "text": """Faculté de Génie des Procédés - Université Constantine 3.
Offre de formation académique accréditée pour l'année universitaire 2024-2025 et 2025-2026 :
1. Master en Génie de l'Environnement et Développement Durable (Diplôme complet dédié à la dépollution, gestion des rejets et technologies vertes).
2. Master en Énergies Renouvelables et Efficacité Énergétique.
Ces cursus diplômants forment chaque année plus de 65 spécialistes directement qualifiés pour relever les défis de la durabilité et des cibles de l'Agenda 2030 de l'ONU."""
    },
    {
        "title": "Programme d'Éducation Ouverte à la Communauté Locale",
        "url_or_path": "https://univ-constantine3.dz/formation-continue/ateliers-durabilite-citoyens-2025/",
        "source_type": "WEB_PAGE",
        "entity": "Direction de la Post-Graduation et Formation Continue UC3",
        "date": "2025-10-05",
        "is_public": True,
        "text": """Université Constantine 3 Salah Boubnider - Ateliers Citoyens de Développement Durable 2025.
Dans le cadre de son ouverture sur la société, l'UC3 organise des sessions de formation gratuites et ouvertes à la communauté locale de la ville de Constantine et Ali Mendjeli.
Thèmes abordés : Techniques d'économie d'eau potable, compostage domestique et gestion des risques de pollution.
Plus de 120 citoyens, artisans et représentants de comités de quartier ont suivi les 4 sessions d'octobre 2025."""
    },
    {
        "title": "Catalogue de Liens Partenariats (Exemple de piège de liens THE)",
        "url_or_path": "https://univ-constantine3.dz/partenariats-links-directory/",
        "source_type": "WEB_PAGE",
        "entity": "Service Relations Extérieures UC3",
        "date": "2025-01-15",
        "is_public": True,
        "text": """Consultez les liens de nos partenaires :
https://www.mesrs.dz/
https://www.sdgaccord.org/members/
https://www.cruo.dz/
https://www.tethys-univ.org/
https://erasmus-plus.dz/
Veuillez cliquer sur les liens ci-dessus pour voir les détails de chaque convention."""
    },
    {
        "title": "Projet de Recherche Conjoint International sur les Données Climat (2022 - Périmé)",
        "url_or_path": "https://vr-recherche.univ-constantine3.dz/projets-archives/climat-2022/",
        "source_type": "WEB_PAGE",
        "entity": "Vice-Rectorat de la Recherche UC3",
        "date": "2022-04-12",
        "is_public": True,
        "text": """Vice-Rectorat de la Recherche Scientifique - UC3.
En avril 2022, l'Université Constantine 3 a finalisé le projet d'échanges de données climatiques régionales avec le réseau euro-méditerranéen.
Ce projet a permis de publier un recueil de métriques environnementales pour l'est algérien."""
    }
]

def load_uc3_sample_corpus(store):
    """Injecte les documents de démonstration dans le KnowledgeStore UC3."""
    for doc in UC3_SAMPLE_DOCUMENTS:
        store.add_document(
            text=doc["text"],
            source_title=doc["title"],
            source_url_or_path=doc["url_or_path"],
            source_type=doc["source_type"],
            entity=doc["entity"],
            date=doc["date"],
            is_public=doc["is_public"]
        )
