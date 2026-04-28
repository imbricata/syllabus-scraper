"""
UB (Universitat de Barcelona) scraper.
Math: https://mat.ub.edu/categ/grau/
Business (ADE): https://www.ub.edu/portal/web/economia-empresa/grau-en-administracio-i-direccio-d-empreses
UB course guides (fitxes docents / guies docents) are linked from degree plan pages.
Guide URLs typically go through: https://www.ub.edu/guiadocent/
"""

import time
import urllib3
urllib3.disable_warnings()

from .base import UniversityScraper


UB_GUIDE_PATTERNS = [
    "guiadocent", "guia-docent", "fitxa", "fitxadocent",
    "docent", "guiadocente",
    "ub.edu/guia",
]

UB_FOLLOW_PATTERNS = [
    "pla", "plan", "estudis", "estudios", "assignatura",
    "asignatura", "grau", "grado", "oferta",
]


class UBScraper(UniversityScraper):

    university = "UB"
    base_url = "https://www.ub.edu"

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        results = []
        program_url = program_cfg["url"]
        program_type = program_cfg["type"]
        label = program_cfg["label"]

        print(f"\n[UB] discovering course guides for {label}")
        print(f"  starting from: {program_url}")

        seen_urls: set[str] = set()

        # UB math is hosted on mat.ub.edu, use that as base
        if "mat.ub.edu" in program_url:
            base_override = "https://mat.ub.edu"
        else:
            base_override = self.base_url

        discovered = self.discover_course_links(
            start_url=program_url,
            url_patterns=UB_GUIDE_PATTERNS,
            follow_patterns=UB_FOLLOW_PATTERNS,
            base_url_override=base_override,
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
