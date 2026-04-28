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
