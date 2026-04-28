"""
UAM scraper, targets Matemáticas and ADE programs.
UAM uses websyllabus.uam.es for course guides, accessible by subject code.
We start from the program study plan page to collect subject codes/links.
"""

import time
from .base import UniversityScraper


class UAMScraper(UniversityScraper):

    university = "UAM"
    base_url = "https://www.uam.es"
    syllabus_base = "https://websyllabus.uam.es"

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        results = []
        program_url = program_cfg["url"]
        program_type = program_cfg["type"]
        label = program_cfg["label"]

        print(f"\n[UAM] scraping {label}")
        soup = self.fetch(program_url)
        if soup is None:
            print(f"  could not reach {program_url}")
            return results

        seen = set()

        # look for links to websyllabus.uam.es (individual course guides)
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if "websyllabus" in href or "guia" in href.lower():
                full_url = href if href.startswith("http") else self.base_url + href
                if full_url not in seen:
                    seen.add(full_url)
                    results.append({
                        "university": self.university,
                        "program": program_name,
                        "program_type": program_type,
                        "course_name": text or full_url,
                        "url": full_url,
                        "format": "html",
                    })

        # also check for direct PDF links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.endswith(".pdf") and href not in seen:
                full_url = href if href.startswith("http") else self.base_url + href
                seen.add(full_url)
                results.append({
                    "university": self.university,
                    "program": program_name,
                    "program_type": program_type,
                    "course_name": a.get_text(strip=True) or full_url,
                    "url": full_url,
                    "format": "pdf",
                })

        # if the study plan page links to sub-pages, follow one level deep
        sub_pages = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "plan" in href.lower() or "estudios" in href.lower():
                full_url = href if href.startswith("http") else self.base_url + href
                if full_url not in seen and self.base_url in full_url:
                    sub_pages.append(full_url)

        for sub_url in sub_pages[:5]:
            seen.add(sub_url)
            time.sleep(0.8)
            sub_soup = self.fetch(sub_url)
            if sub_soup is None:
                continue
            for a in sub_soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)
                if "websyllabus" in href or href.endswith(".pdf"):
                    full_url = href if href.startswith("http") else self.base_url + href
                    if full_url not in seen:
                        seen.add(full_url)
                        results.append({
                            "university": self.university,
                            "program": program_name,
                            "program_type": program_type,
                            "course_name": text or full_url,
                            "url": full_url,
                            "format": "pdf" if href.endswith(".pdf") else "html",
                        })

        print(f"  found {len(results)} links for {label}")
        return results
