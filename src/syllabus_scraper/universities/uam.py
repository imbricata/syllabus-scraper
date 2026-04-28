"""
UAM scraper. Course guides live at the virtual secretariat:
  https://secretaria-virtual.uam.es/doa/consultaPublica/look[conpub]MostrarPubGuiaDocAs
  ?_anoAcademico=2025&_codAsignatura=CODE&entradaPublica=true&idiomaPais=es.ES

Discovery approach: scrape the program/plan de estudios page looking for links
to secretaria-virtual.uam.es or guías docentes PDFs.
"""

import time
import urllib3
urllib3.disable_warnings()

from .base import UniversityScraper


UAM_GUIDE_PATTERNS = [
    "secretaria-virtual.uam.es",
    "consultapublica",
    "guiadoc",
    "guia-docente",
    "ficha",
]

UAM_FOLLOW_PATTERNS = [
    "plan", "estudios", "asignatura", "grado",
    "programa", "docencia", "titulacion",
]


class UAMScraper(UniversityScraper):

    university = "UAM"
    base_url = "https://www.uam.es"

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        results = []
        program_type = program_cfg["type"]
        label = program_cfg["label"]
        program_url = program_cfg["url"]

        print(f"\n[UAM] discovering course guides for {label}")
        print(f"  starting from: {program_url}")

        seen_urls: set[str] = set()

        discovered = self.discover_course_links(
            start_url=program_url,
            url_patterns=UAM_GUIDE_PATTERNS,
            follow_patterns=UAM_FOLLOW_PATTERNS,
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

        # try the course guide base URL directly if config includes it
        guide_base = program_cfg.get("course_guide_base", "")
        if guide_base and len(results) < 5:
            print(f"  trying course guide base: {guide_base}")
            soup = self.fetch(guide_base)
            if soup:
                for text, url in self._extract_from_soup(soup, seen_urls, program_name, program_type):
                    results.append(url)

        print(f"  found {len(results)} course guide links for {label}")
        return results

    def _extract_from_soup(self, soup, seen_urls, program_name, program_type):
        out = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if not text:
                continue
            href_lower = href.lower()
            if any(p in href_lower for p in UAM_GUIDE_PATTERNS) or href.endswith(".pdf"):
                fu = href if href.startswith("http") else self.base_url + href
                if fu not in seen_urls:
                    seen_urls.add(fu)
                    fmt = "pdf" if href.endswith(".pdf") else "html"
                    out.append((text, {
                        "university": self.university,
                        "program": program_name,
                        "program_type": program_type,
                        "course_name": text,
                        "url": fu,
                        "format": fmt,
                    }))
        return out
