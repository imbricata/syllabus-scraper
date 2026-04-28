"""
UGR (Universidad de Granada) scraper.
Math course guide index: https://grados.ugr.es/matematicas/pages/infoacademica/guiasdocentes
Business course guide index: https://grados.ugr.es/administracionempresas/pages/infoacademica/guiasdocentes
Individual guides are HTML pages linked from those index pages.
"""

import time
import urllib3
urllib3.disable_warnings()

from .base import UniversityScraper


UGR_GUIDE_PATTERNS = [
    "guia-docente", "guiadocente", "guias-docentes",
    "/docencia/plan-estudios/",
    "ficha-asignatura",
]

UGR_FOLLOW_PATTERNS = [
    "infoacademica", "guias", "plan", "asignatura",
    "estudios", "grado",
]


class UGRScraper(UniversityScraper):

    university = "UGR"
    base_url = "https://grados.ugr.es"

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        results = []
        program_url = program_cfg["url"]
        program_type = program_cfg["type"]
        label = program_cfg["label"]

        # UGR provides a specific guide index URL, prefer it if given
        guide_index = program_cfg.get("guide_index", program_url)

        print(f"\n[UGR] discovering course guides for {label}")
        print(f"  starting from: {guide_index}")

        seen_urls: set[str] = set()

        discovered = self.discover_course_links(
            start_url=guide_index,
            url_patterns=UGR_GUIDE_PATTERNS,
            follow_patterns=UGR_FOLLOW_PATTERNS,
            base_url_override=self.base_url,
            max_depth=2,
            min_links=3,
        )

        for text, url in discovered:
            # skip the index page itself
            if "guiasdocentes" in url and url == guide_index:
                continue
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
