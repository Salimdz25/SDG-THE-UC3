"""
Module de Collecte Web pour l'Université Constantine 3 (UC3)
Exploration ciblée des domaines institutionnels :
- *.univ-constantine3.dz (Rectorat, Faculté de Médecine, Faculté Génie des Procédés, etc.)
- Respect strict de la visibilité publique et traçabilité de consultation
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

ALLOWED_DOMAINS = [
    "univ-constantine3.dz",
    "facmed-univ-constantine3.dz",
    "vr-recherche.univ-constantine3.dz",
    "fac-gp.univ-constantine3.dz",
    "fac-archi.univ-constantine3.dz",
    "local-mock.univ-constantine3.dz"
]

class UC3WebCrawler:
    def __init__(self, allowed_domains: Optional[List[str]] = None, timeout: int = 10):
        self.allowed_domains = allowed_domains or ALLOWED_DOMAINS
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "UC3-Sustainability-Ratings-Collector/1.0 (+http://univ-constantine3.dz)"
        })

    def is_allowed_url(self, url: str) -> bool:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if not domain:
            return False
        return any(domain == d or domain.endswith("." + d) for d in self.allowed_domains)

    def fetch_page(self, url: str) -> Dict[str, Any]:
        """
        Récupère et structure le contenu d'une page institutionnelle UC3.
        Conserve impérativement la date de consultation et l'URL source.
        """
        fetch_time = datetime.now().isoformat()
        try:
            if urlparse(url).scheme != "https" or not self.is_allowed_url(url):
                raise ValueError("Adresse HTTPS hors des domaines institutionnels autorisés")
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=False)
            if 300 <= resp.status_code < 400:
                raise ValueError("Redirection non autorisée : vérifiez la destination séparément")
            resp.raise_for_status()
            if "text/html" not in resp.headers.get("Content-Type", ""):
                raise ValueError("La source ne fournit pas une page HTML lisible")
            html = resp.text
            return self.parse_html(html, url=url, fetch_timestamp=fetch_time)
        except Exception as e:
            return {
                "url": url,
                "status": "error",
                "error_message": str(e),
                "fetch_timestamp": fetch_time,
                "full_text": ""
            }

    def parse_html(self, html: str, url: str = "", fetch_timestamp: Optional[str] = None) -> Dict[str, Any]:
        fetch_time = fetch_timestamp or datetime.now().isoformat()
        soup = BeautifulSoup(html, "html.parser")

        # Nettoyage des balises script, style, nav et footer
        for tag in soup(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        
        # Récupération des titres h1, h2, h3 pour hiérarchie
        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])]
        
        # Récupération des paragraphes et listes
        paragraphs = [p.get_text(strip=True) for p in soup.find_all(["p", "li"]) if len(p.get_text(strip=True)) > 20]
        full_text = "\n\n".join(paragraphs)

        # Détection des liens présents pour vérifier l'autosuffisance
        links = []
        for a in soup.find_all("a", href=True):
            links.append({"text": a.get_text(strip=True), "href": a["href"]})

        # Détection date dans le document
        return {
            "source_type": "WEB_PAGE",
            "url": url,
            "title": title,
            "headings": headings,
            "fetch_timestamp": fetch_time,
            "full_text": full_text,
            "links_count": len(links),
            "status": "success",
            "is_public": True
        }
