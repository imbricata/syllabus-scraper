"""
UC3M scraper, targets Applied Mathematics and Business programs.
UC3M publishes course syllabuses as PDFs linked from the study plan page.
"""

import time
from .base import UniversityScraper


class UC3MScraper(UniversityScraper):

    university = "UC3M"
    base_url = "https://www.uc3m.es"

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        results = []
        program_url = program_cfg["url"]
        program_type = program_cfg["type"]
        label = program_cfg["label"]

        print(f"\n[UC3M] scraping {label}")
        soup = self.fetch(program_url)
        if soup is None:
            print(f"  could not reach {program_url}")
            return results

        # UC3M study plan pages list subjects with links to course info pages
        # course info pages contain a link to the PDF syllabus
        course_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            # UC3M course pages are under /ss/Satellite or /estudios
            if any(k in href for k in ["/ss/Satellite", "course", "subject", "asignatura"]):
                full_url = href if href.startswith("http") else self.base_url + href
                if text:
                    course_links.append((text, full_url))

        # also grab any direct PDF links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.endswith(".pdf"):
                full_url = href if href.startswith("http") else self.base_url + href
                results.append({
                    "university": self.university,
                    "program": program_name,
                    "program_type": program_type,
                    "course_name": a.get_text(strip=True) or full_url,
                    "url": full_url,
                    "format": "pdf",
                })

        # follow course pages to get PDF links
        seen = set()
        for course_name, course_url in course_links[:40]:
            if course_url in seen:
                continue
            seen.add(course_url)

            time.sleep(0.8)
            course_soup = self.fetch(course_url)
            if course_soup is None:
                continue

            pdf_links = self.find_pdf_links(course_soup, self.base_url)
            for pdf_url in pdf_links:
                results.append({
                    "university": self.university,
                    "program": program_name,
                    "program_type": program_type,
                    "course_name": course_name,
                    "url": pdf_url,
                    "format": "pdf",
                })

        print(f"  found {len(results)} links for {label}")
        return results
