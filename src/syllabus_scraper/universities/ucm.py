"""
UCM scraper, targets Matemáticas and ADE programs.
UCM publishes guías docentes as HTML pages under ucm.es/estudios.
We grab course links from the plan de estudios page, then follow each
course page to find the guía docente link or PDF.
"""

import time
from .base import UniversityScraper


class UCMScraper(UniversityScraper):

    university = "UCM"
    base_url = "https://www.ucm.es"

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        results = []
        program_url = program_cfg["url"]
        program_type = program_cfg["type"]
        label = program_cfg["label"]

        print(f"\n[UCM] scraping {label}")
        soup = self.fetch(program_url)
        if soup is None:
            print(f"  could not reach {program_url}")
            return results

        # UCM plan de estudios pages list courses as links
        # look for links containing keywords that indicate course guides
        course_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            # guías docentes are linked from the course name or a "guía" link
            if any(k in href.lower() for k in ["guia", "guía", "course", "asignatura"]):
                full_url = href if href.startswith("http") else self.base_url + href
                course_links.append((text, full_url))

        # also grab PDF links directly
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

        # follow each course page to find PDFs or HTML guides
        seen = set()
        for course_name, course_url in course_links[:40]:  # cap to avoid hammering
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
