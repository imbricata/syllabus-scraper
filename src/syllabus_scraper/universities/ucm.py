"""
UCM scraper. Fetches course guide links from the plan de estudios pages.
UCM course guides (fichas docentes) are HTML pages linked from subject entries.
"""

import re
import time
import urllib3
urllib3.disable_warnings()

from .base import UniversityScraper


class UCMScraper(UniversityScraper):

    university = "UCM"
    base_url = "https://matematicas.ucm.es"

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        results = []
        program_url = program_cfg["url"]
        program_type = program_cfg["type"]
        label = program_cfg["label"]

        # resolve base_url per program
        if "economicasyempresariales" in program_url:
            base = "https://economicasyempresariales.ucm.es"
        else:
            base = "https://matematicas.ucm.es"

        print(f"\n[UCM] scraping {label}")
        soup = self.fetch(program_url)
        if soup is None:
            print(f"  could not reach {program_url}")
            return results

        seen = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)

            # course guide links at UCM typically contain 'ficha', 'guia', 'docente', or subject codes
            if not text:
                continue
            if any(k in href.lower() for k in ["ficha", "guia", "guía", "docente", "asignatura"]):
                full_url = href if href.startswith("http") else base + href
                if full_url not in seen:
                    seen.add(full_url)
                    results.append({
                        "university": self.university,
                        "program": program_name,
                        "program_type": program_type,
                        "course_name": text,
                        "url": full_url,
                        "format": "html",
                    })

            # also grab direct PDF course guides
            if href.endswith(".pdf"):
                pdf_url = href if href.startswith("http") else base + href
                if pdf_url not in seen:
                    seen.add(pdf_url)
                    results.append({
                        "university": self.university,
                        "program": program_name,
                        "program_type": program_type,
                        "course_name": text,
                        "url": pdf_url,
                        "format": "pdf",
                    })

        # if sparse, follow one level into sub-pages that list subjects
        if len(results) < 5:
            sub_urls = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if any(k in href.lower() for k in ["plan", "curso", "primer", "segundo", "tercer", "cuarto"]):
                    full_url = href if href.startswith("http") else base + href
                    if full_url not in seen and base in full_url:
                        sub_urls.append((a.get_text(strip=True), full_url))

            for sub_text, sub_url in sub_urls[:6]:
                seen.add(sub_url)
                time.sleep(0.8)
                sub_soup = self.fetch(sub_url)
                if not sub_soup:
                    continue
                for a in sub_soup.find_all("a", href=True):
                    href = a["href"]
                    text = a.get_text(strip=True)
                    if not text:
                        continue
                    if any(k in href.lower() for k in ["ficha", "guia", "guía", "docente"]):
                        full_url = href if href.startswith("http") else base + href
                        if full_url not in seen:
                            seen.add(full_url)
                            results.append({
                                "university": self.university,
                                "program": program_name,
                                "program_type": program_type,
                                "course_name": text,
                                "url": full_url,
                                "format": "html",
                            })

        print(f"  found {len(results)} links for {label}")
        return results
