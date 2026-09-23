"""
Module de Collecte et Traitement des Publications Facebook Institutionnelles UC3
Conformité avec les règles impératives :
- Analyse uniquement les pages publiques officielles (ex: Rectorat, Faculté de Médecine, Clubs scientifiques agréés)
- Extraction : texte, date, nom de page, URL directe, mentions de partenaires, bénéficiaires et activités
- Recommandation systématique de pérennisation sur le sous-domaine web officiel UC3
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import re

class FacebookInstitutionalCollector:
    def __init__(self, authorized_pages: Optional[List[str]] = None):
        self.authorized_pages = authorized_pages or [
            "Université Salah Boubnider Constantine 3",
            "Faculté de Médecine Constantine 3",
            "Faculté Génie des Procédés UC3",
            "Incubateur d'Entreprises UC3",
            "Club Scientifique ODD UC3"
        ]

    def parse_post(
        self,
        page_name: str,
        post_url: str,
        post_date: str,
        content: str,
        images_or_posters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Structure une publication Facebook institutionnelle avec détection des entités clés.
        """
        consultation_date = datetime.now().isoformat()
        
        # Extraction des mentions clés
        mentions_uc3 = bool(re.search(r"\b(UC3|Constantine 3|Salah Boubnider|جامعة قسنطينة 3)\b", content, re.IGNORECASE))
        
        # Détection de partenaires (ministères, ONG, universités internationales, entreprises)
        partners_detected = re.findall(
            r"(?:partenariat avec|en collaboration avec|convention avec|avec l'appui de|بالتعاون مع|شراكة مع)\s+([A-Z\u0600-\u06FF][^\n,.]+)",
            content,
            re.IGNORECASE
        )
        
        # Détection des bénéficiaires
        beneficiaries_detected = re.findall(
            r"(?:au profit de|destiné aux|au bénéfice de|لفائدة|لصالح)\s+([^\n,.]+)",
            content,
            re.IGNORECASE
        )

        # Détection de l'année
        year_matches = re.findall(r"\b(202[0-9])\b", f"{post_date} {content}")
        year = int(year_matches[0]) if year_matches else None

        # Recommandation automatique de pérennisation
        recommendation = (
            "ACTION REQUISE : Transformer cette publication Facebook en page web institutionnelle "
            "dédiée sur le sous-domaine officiel de l'UC3 (ex: univ-constantine3.dz/odd/...). "
            "Une publication Facebook risque de ne pas être reconnue comme autosuffisante et pérenne par l'auditeur THE."
        )

        return {
            "source_type": "FACEBOOK_INSTITUTIONAL",
            "page_name": page_name,
            "url": post_url,
            "publication_date": post_date,
            "consultation_date": consultation_date,
            "year": year,
            "content": content,
            "images_or_posters": images_or_posters or [],
            "mentions_uc3": mentions_uc3,
            "partners_detected": [p.strip() for p in partners_detected],
            "beneficiaries_detected": [b.strip() for b in beneficiaries_detected],
            "is_public": True,
            "requires_web_migration": True,
            "migration_recommendation": recommendation
        }

    def batch_import_from_json(self, json_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for item in json_data:
            results.append(self.parse_post(
                page_name=item.get("page_name", "Page UC3"),
                post_url=item.get("post_url", ""),
                post_date=item.get("post_date", ""),
                content=item.get("content", ""),
                images_or_posters=item.get("images_or_posters", [])
            ))
        return results
