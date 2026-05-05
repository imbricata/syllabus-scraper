import requests
from bs4 import BeautifulSoup
import pdfplumber
import pandas as pd
import re
import os
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


DEGREE_PAGES = {
    "matematicas": "https://matematicas.epes.upm.es/el-grado/plan-de-estudios/",
    "informatica": "https://www.fi.upm.es/?pagina=3055",
    "ciencia-datos": "https://www.etsiinf.upm.es/?pagina=3059",
}

PDF_KEYWORD = "comun_gauss/publico/guias"
DOWNLOAD_DIR = "data/raw/upm"


def get_pdf_links(degree_slug, page_url):
    print(f"\n  Fetching: {page_url}")
    try:
        response = requests.get(page_url, timeout=15, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")

        links = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if PDF_KEYWORD in href and href.endswith(".pdf") and href not in seen:
                seen.add(href)
                course_name = a.text.strip()
                links.append((course_name, href))
                print(f"    Found: {course_name}")

        print(f"  Total PDFs found: {len(links)}")
        return links

    except Exception as e:
        print(f"  Error: {e}")
        return []


def download_pdf(url, dest_path):
    try:
        response = requests.get(url, timeout=15, verify=False)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                f.write(response.content)
            return True
        return False
    except Exception as e:
        print(f"  Download error: {e}")
        return False


def parse_grading(pdf_path):
    results = {
        "midterm_tests": 0,
        "project": 0,
        "participation": 0,
        "other": 0,
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            progresiva_page = None

            for i, page in enumerate(pdf.pages):
                text = (page.extract_text() or "").lower()
                if "evaluación (progresiva)" in text or "evaluacion (progresiva)" in text:
                    progresiva_page = i
                    break

            if progresiva_page is None:
                return results

            for i in range(progresiva_page, min(progresiva_page + 3, len(pdf.pages))):
                page = pdf.pages[i]
                tables = page.extract_tables()

                for table in tables:
                    if not table:
                        continue

                    # Skip table if it contains 100% (global exam table)
                    is_global = any(
                        len(row) > 5 and str(row[5]).strip() == "100%"
                        for row in table if row
                    )
                    if is_global:
                        continue

                    for row in table:
                        if not row or len(row) < 6:
                            continue

                        cleaned = [str(c).strip() if c else "" for c in row]

                        # Skip semester 17 rows (final exam week)
                        sem = cleaned[0].strip()
                        if sem == "17":
                            continue

                        pct_cell = cleaned[5]
                        m = re.search(r"(\d+(?:\.\d+)?)\s*%", pct_cell)
                        if not m:
                            continue

                        pct = float(m.group(1))
                        if pct >= 100:
                            continue

                        tipo = cleaned[2].lower()
                        desc = cleaned[1].lower()

                        if "ex:" in tipo or "examen" in tipo or "examen" in desc or "parcial" in desc:
                            results["midterm_tests"] += pct
                        elif "tg:" in tipo or "trabajo en grupo" in tipo:
                            results["project"] += pct
                        elif "ep:" in tipo or "laboratorio" in tipo or "prácticas" in desc or "práctica" in desc:
                            results["other"] += pct
                        elif "pl:" in tipo:
                            results["other"] += pct
                        elif "ot:" in tipo:
                            results["participation"] += pct
                        else:
                            results["other"] += pct

    except Exception as e:
        print(f"  Parse error {pdf_path}: {e}")

    return results

def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    all_rows = []

    for degree_slug, page_url in DEGREE_PAGES.items():
        print(f"\n{'='*50}")
        print(f"Degree: {degree_slug}")

        pdf_links = get_pdf_links(degree_slug, page_url)

        if not pdf_links:
            print(f"  No PDFs found for {degree_slug}")
            continue

        for course_name, pdf_url in pdf_links:
            filename = f"{degree_slug}__{pdf_url.split('/')[-1]}"
            dest_path = os.path.join(DOWNLOAD_DIR, filename)

            if not os.path.exists(dest_path):
                success = download_pdf(pdf_url, dest_path)
                if not success:
                    continue
                time.sleep(0.3)

            grading = parse_grading(dest_path)
            total = sum(grading.values())

            row = {
                "university": "UPM",
                "degree": degree_slug,
                "course_name": course_name,
                **grading,
                "total_weight": total,
                "parse_status": "ok" if 90 <= total <= 110 else "needs_review",
            }
            all_rows.append(row)
            print(f"  {course_name}: exams={grading['midterm_tests']}% project={grading['project']}% other={grading['other']}% total={total}%")

    df = pd.DataFrame(all_rows)
    out_path = "data/processed/upm_grading_dataframe.csv"
    df.to_csv(out_path, index=False)

    print(f"\n✅ Done! Scraped {len(df)} courses across {len(DEGREE_PAGES)} degrees.")
    print(f"Saved to {out_path}")

    if not df.empty:
        ok = df[df["parse_status"] == "ok"]
        print("\nAverage exam weight by degree:")
        print(ok.groupby("degree")["midterm_tests"].mean().sort_values(ascending=False).round(1))


if __name__ == "__main__":
    main()