"""
URJC (Universidad Rey Juan Carlos) scraper.
Math: https://www.urjc.es/estudios/grado/1067-grado-en-matematicas
ADE:  https://www.urjc.es/estudios/grado/742-grado-en-administracion-y-direccion-de-empresas

URJC course guides are served via:
  https://gestion3.urjc.es/guiasdocentes/

Discovery: scrape program page to find a link to gestion3.urjc.es/guiasdocentes,
then follow that portal page looking for individual course guide links.
"""

import time
import re
import urllib3
urllib3.disable_warnings()

from .base import UniversityScraper


URJC_GUIDE_PORTAL_PATTERNS = [
    "gestion3.urjc.es/guiasdocentes",
    "guiasdocentes",
]

URJC_GUIDE_PATTERNS = [
    "guia", "guiadocente", "asignatura",
    "gestion3.urjc.es",
]

URJC_FOLLOW_PATTERNS = [
    "plan", "estudios", "asignatura", "programa",
    "grado", "curso", "guias",
]


class URJCScraper(UniversityScraper):

    university = "URJC"
    base_url = "https://www.urjc.es"

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        results = []
        program_url = program_cfg["url"]
        program_type = program_cfg["type"]
        label = program_cfg["label"]

        print(f"\n[URJC] discovering course guides for {label}")
        print(f"  starting from: {program_url}")

        seen_urls: set[str] = set()

        # step 1: scrape program page to find the guide portal link
        soup = self.fetch(program_url)
        portal_url = None
        if soup:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if any(p in href.lower() for p in URJC_GUIDE_PORTAL_PATTERNS):
                    portal_url = href if href.startswith("http") else self.base_url + href
                    break

        if portal_url:
            print(f"  found guide portal: {portal_url}")
            # step 2: scrape the portal page for individual course guide links
            portal_soup = self.fetch(portal_url)
            if portal_soup:
                for a in portal_soup.find_all("a", href=True):
                    href = a["href"]
                    text = a.get_text(strip=True)
                    if not text or len(text) < 3:
                        continue
                    href_lower = href.lower()
                    if any(p in href_lower for p in URJC_GUIDE_PATTERNS) or href.endswith(".pdf"):
                        fu = href if href.startswith("http") else "https://gestion3.urjc.es" + href
                        if fu not in seen_urls:
                            seen_urls.add(fu)
                            fmt = "pdf" if fu.endswith(".pdf") else "html"
                            results.append({
                                "university": self.university,
                                "program": program_name,
                                "program_type": program_type,
                                "course_name": text,
                                "url": fu,
                                "format": fmt,
                            })

        # fallback: generic discovery from program page
        if len(results) < 3:
            discovered = self.discover_course_links(
                start_url=program_url,
                url_patterns=URJC_GUIDE_PATTERNS,
                follow_patterns=URJC_FOLLOW_PATTERNS,
                base_url_override=self.base_url,
                max_depth=2,
                min_links=3,
            )
            for text, url in discovered:
                if url not in seen_urls:
                    seen_urls.add(url)
                    fmt = "pdf" if url.endswith(".pdf") else "html"
                    results.append({
                        "university": self.university,
                        "program": program_name,
                        "program_type": program_type,
                        "course_name": text,
                        "url": url,
                        "format": fmt,
                    })

        print(f"  found {len(results)} course guide links for {label}")
        return results
