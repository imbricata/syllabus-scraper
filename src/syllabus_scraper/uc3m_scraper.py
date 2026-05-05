import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


DEGREES = {
    "matematica-aplicada": ("507", "554"),
    "matematicas": ("350", "478"),
    "ingenieria-informatica": ("350", "379"),
    "administracion-empresas": ("350", "373"),
    "derecho": ("350", "374"),
    "economia": ("350", "375"),
    "estadistica-empresa": ("350", "376"),
    "ingenieria-electronica": ("350", "380"),
    "ingenieria-mecanica": ("350", "381"),
    "comunicacion-audiovisual": ("350", "383"),
    "periodismo": ("350", "384"),
    "historia-politica": ("350", "388"),
    "filosofia-politica-economia": ("350", "389"),
    "relaciones-laborales": ("350", "390"),
    "ciencias-politicas": ("350", "391"),
    "turismo": ("350", "393"),
}

YEAR = "2025"
LANGUAGE = "1"


def get_course_links(degree_slug):
    url = f"https://www.uc3m.es/grado/{degree_slug}"
    print(f"\n  Fetching: {url}")

    try:
        response = requests.get(url, timeout=15, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")

        course_links = []
        seen = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "generaFicha" in href and "asig=" in href:
                if href.startswith("http"):
                    full_url = href
                else:
                    full_url = "https://aplicaciones.uc3m.es" + href

                if full_url not in seen:
                    seen.add(full_url)
                    course_name = a.text.strip()
                    course_links.append((course_name, full_url))

        print(f"  Found {len(course_links)} courses")
        return course_links

    except Exception as e:
        print(f"  Error: {e}")
        return []


def get_grading_from_course(course_name, course_url):
    try:
        response = requests.get(course_url, timeout=15, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Get all plain text from the page
        text = soup.get_text(separator=" ", strip=True)

        final_match = re.search(
            r"Peso porcentual del Examen[/\s]Prueba Final\s*(\d+)", text
        )
        continuous_match = re.search(
            r"Peso porcentual del resto de la evaluaci[oó]n\s*(\d+)", text
        )

        final_pct = int(final_match.group(1)) if final_match else 0
        continuous_pct = int(continuous_match.group(1)) if continuous_match else 0
        total = final_pct + continuous_pct

        return {
            "course_name": course_name,
            "course_url": course_url,
            "final_exam": final_pct,
            "continuous_evaluation": continuous_pct,
            "total_weight": total,
            "parse_status": "ok" if 90 <= total <= 110 else "needs_review",
        }

    except Exception as e:
        print(f"  Error fetching {course_url}: {e}")
        return None

def main():
    all_rows = []

    for degree_slug in DEGREES:
        print(f"\nScraping: {degree_slug}")
        course_links = get_course_links(degree_slug)

        for course_name, course_url in course_links:
            result = get_grading_from_course(course_name, course_url)
            if result:
                result["degree"] = degree_slug
                result["university"] = "UC3M"
                all_rows.append(result)
                print(f"    {course_name}: final={result['final_exam']}% continuous={result['continuous_evaluation']}%")
            time.sleep(0.3)

    df = pd.DataFrame(all_rows)
    out_path = "data/processed/uc3m_grading_dataframe.csv"
    df.to_csv(out_path, index=False)

    print(f"\n✅ Done! Scraped {len(df)} courses across {len(DEGREES)} degrees.")
    print(f"Saved to {out_path}")

    if not df.empty and "parse_status" in df.columns:
        print("\nAverage final exam weight by degree:")
        result = df[df["parse_status"] == "ok"].groupby("degree")["final_exam"].mean()
        print(result.sort_values(ascending=False).round(1))


if __name__ == "__main__":
    main()