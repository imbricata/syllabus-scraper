"""
UC3M scraper. Course guides live at:
  https://aplicaciones.uc3m.es/cpa/generaFicha?est=PROG&asig=CODE&idioma=1

Discovery approach: scrape the program page and plan de estudios sub-pages
looking for links that point to aplicaciones.uc3m.es/cpa/generaFicha.
"""

import time
import urllib3
urllib3.disable_warnings()

from .base import UniversityScraper


# URL patterns that identify a UC3M course guide link
UC3M_GUIDE_PATTERNS = ["generaficha", "aplicaciones.uc3m.es/cpa"]

# sub-page patterns worth following when main page is sparse
UC3M_FOLLOW_PATTERNS = [
    "plan", "asignatura", "estudios", "grado", "programa",
    "oferta", "curso", "docencia",
]


class UC3MScraper(UniversityScraper):

    university = "UC3M"
    base_url = "https://www.uc3m.es"

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        results = []
        program_type = program_cfg["type"]
        label = program_cfg["label"]
        program_url = program_cfg["url"]

        print(f"\n[UC3M] discovering course guides for {label}")
        print(f"  starting from: {program_url}")

        seen_urls: set[str] = set()

        # discover from the program page (and sub-pages if needed)
        discovered = self.discover_course_links(
            start_url=program_url,
            url_patterns=UC3M_GUIDE_PATTERNS,
            follow_patterns=UC3M_FOLLOW_PATTERNS,
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

        # also try the program's "plan de estudios" URL if the main page yielded little
        if len(results) < 5:
            plan_suffixes = [
                "/estudios/plan-de-estudios",
                "/estudios",
                "/asignaturas",
            ]
            for suffix in plan_suffixes:
                alt_url = program_url.rstrip("/") + suffix
                time.sleep(0.5)
                sub = self.discover_course_links(
                    start_url=alt_url,
                    url_patterns=UC3M_GUIDE_PATTERNS,
                    max_depth=1,
                )
                for text, url in sub:
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
                if len(results) >= 5:
                    break

        print(f"  found {len(results)} course guide links for {label}")
        return results
