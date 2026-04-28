"""
Comillas Universidad Pontificia scraper.
Covers both ICAI (engineering/math) and ICADE (business).
ICAI math:     https://www.comillas.edu/grados/grado-en-ingenieria-matematica-e-inteligencia-ar
ICADE business: https://www.comillas.edu/grados/grado-en-administracion-y-direccion-de-empresas-
Course guides are HTML pages linked from the degree program pages.
"""

import time
import urllib3
urllib3.disable_warnings()

from .base import UniversityScraper


COMILLAS_GUIDE_PATTERNS = [
    "guia", "guía", "ficha", "docente",
    "asignatura", "planestudios",
    "repositorio.comillas.edu",
    "sifo.comillas.edu",
]

COMILLAS_FOLLOW_PATTERNS = [
    "plan", "estudios", "asignatura", "programa",
    "grado", "curso", "ingenieria", "administracion",
]


class ComillasScraper(UniversityScraper):

    university = "Comillas"
    base_url = "https://www.comillas.edu"

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        results = []
        program_url = program_cfg["url"]
        program_type = program_cfg["type"]
        label = program_cfg["label"]

        print(f"\n[Comillas] discovering course guides for {label}")
        print(f"  starting from: {program_url}")

        seen_urls: set[str] = set()

        discovered = self.discover_course_links(
            start_url=program_url,
            url_patterns=COMILLAS_GUIDE_PATTERNS,
            follow_patterns=COMILLAS_FOLLOW_PATTERNS,
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
