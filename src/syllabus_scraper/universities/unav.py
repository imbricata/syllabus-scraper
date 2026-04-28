"""
UNAV (Universidad de Navarra) scraper.
Math: https://www.unav.edu/web/facultad-de-ciencias/grado-en-matematicas
ADE:  https://www.unav.edu/web/facultad-de-ciencias-economicas-y-empresariales/grado-en-administracion-y-direccion-de-empresas
UNAV course guides are HTML pages typically linked from the program's course listing.
"""

import time
import urllib3
urllib3.disable_warnings()

from .base import UniversityScraper


UNAV_GUIDE_PATTERNS = [
    "guia", "guía", "ficha", "docente",
    "asignatura", "planestudios",
    "unav.edu/web", "unav.edu/portal",
]

UNAV_FOLLOW_PATTERNS = [
    "plan", "estudios", "asignatura", "programa",
    "grado", "curso", "matematicas", "empresa",
]


class UNAVScraper(UniversityScraper):

    university = "UNAV"
    base_url = "https://www.unav.edu"

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        results = []
        program_url = program_cfg["url"]
        program_type = program_cfg["type"]
        label = program_cfg["label"]

        print(f"\n[UNAV] discovering course guides for {label}")
        print(f"  starting from: {program_url}")

        seen_urls: set[str] = set()

        discovered = self.discover_course_links(
            start_url=program_url,
            url_patterns=UNAV_GUIDE_PATTERNS,
            follow_patterns=UNAV_FOLLOW_PATTERNS,
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
