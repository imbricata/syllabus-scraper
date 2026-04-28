import re
import time
import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


class UniversityScraper:
    """
    Base class for all university scrapers.
    Each subclass implements get_syllabus_links() for its own URL structure.
    Returns a list of dicts: {university, program, program_type, course_name, url}
    """

    university = ""
    base_url = ""

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        raise NotImplementedError

    def fetch(self, url: str, retries: int = 3, delay: float = 1.5) -> BeautifulSoup | None:
        for attempt in range(retries):
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
                resp.raise_for_status()
                return BeautifulSoup(resp.text, "lxml")
            except Exception as e:
                print(f"  fetch error ({url}): {e}, attempt {attempt + 1}/{retries}")
                time.sleep(delay)
        return None

    def fetch_text(self, url: str) -> str:
        soup = self.fetch(url)
        return soup.get_text(separator="\n") if soup else ""

    def find_pdf_links(self, soup: BeautifulSoup, base_url: str = "") -> list[str]:
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.endswith(".pdf"):
                if href.startswith("http"):
                    links.append(href)
                elif base_url:
                    links.append(base_url.rstrip("/") + "/" + href.lstrip("/"))
        return links

    def discover_course_links(
        self,
        start_url: str,
        url_patterns: list[str],
        follow_patterns: list[str] | None = None,
        base_url_override: str = "",
        max_depth: int = 2,
        min_links: int = 3,
    ) -> list[tuple[str, str]]:
        """
        Crawl start_url (and optionally one level deeper) looking for course guide links.
        url_patterns: substrings that identify a course guide URL (checked lowercase)
        follow_patterns: substrings that identify a sub-page worth following (like 'plan', 'asignatura')
        Returns list of (link_text, full_url) tuples — no hardcoded course codes.
        """
        base = base_url_override or self.base_url
        seen: set[str] = set([start_url])
        results: list[tuple[str, str]] = []

        def make_full(href: str) -> str:
            if href.startswith("http"):
                return href
            if href.startswith("//"):
                return "https:" + href
            return base.rstrip("/") + "/" + href.lstrip("/")

        def extract_guide_links(soup: BeautifulSoup) -> list[tuple[str, str]]:
            found = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)
                if not text or len(text) < 3:
                    continue
                href_lower = href.lower()
                if any(p in href_lower for p in url_patterns):
                    fu = make_full(href)
                    if fu not in seen:
                        seen.add(fu)
                        found.append((text, fu))
                # always grab PDFs that haven't been seen
                if href_lower.endswith(".pdf"):
                    fu = make_full(href)
                    if fu not in seen:
                        seen.add(fu)
                        found.append((text, fu))
            return found

        soup = self.fetch(start_url)
        if soup is None:
            return results

        results.extend(extract_guide_links(soup))

        if len(results) < min_links and follow_patterns and max_depth > 1:
            sub_candidates = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                href_lower = href.lower()
                if any(p in href_lower for p in follow_patterns):
                    fu = make_full(href)
                    # only follow internal links
                    if fu not in seen and (base.split("//")[1].split("/")[0] in fu or fu.startswith("/")):
                        sub_candidates.append(fu)
                        seen.add(fu)

            for sub_url in sub_candidates[:8]:
                time.sleep(0.6)
                sub_soup = self.fetch(sub_url)
                if sub_soup:
                    new = extract_guide_links(sub_soup)
                    results.extend(new)
                    if len(results) >= 10:
                        break

        return results
