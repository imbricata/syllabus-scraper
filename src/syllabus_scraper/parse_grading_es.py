"""
Spanish-language grading parser.
Same structure as parse_grading.py but handles Spanish syllabuses,
keywords like 'examen final', 'evaluacion', 'practicas', etc.
"""

import re
import pdfplumber
import requests


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

EVAL_SECTION_MARKERS = [
    "criterios de evaluación",
    "sistema de evaluación",
    "evaluación",
    "evaluacion",
    "métodos de evaluación",
    "procedimiento de evaluación",
    "assessment",           # some Spanish unis use English sections
    "evaluation criteria",
]

END_MARKERS = [
    "bibliografía", "bibliografia", "recursos", "tutorías", "tutorias",
    "metodología", "metodologia", "competencias", "temario", "programa",
    "re-sit", "ai policy", "attendance",
]


def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def map_label_es(label: str) -> str | None:
    label = normalize(label)
    label = re.sub(r"^[a-z0-9]\.", "", label).strip()

    if not label or label in ("criterio", "criterios", "actividad", "porcentaje",
                               "peso", "nota", "tipo de prueba", "descripción"):
        return None

    # final exam
    if any(k in label for k in ["examen final", "prueba final", "examen global",
                                  "examen presencial", "final exam", "final test",
                                  "prueba de evaluación final"]):
        return "final_exam"

    # midterm
    if any(k in label for k in ["examen parcial", "prueba parcial", "parcial",
                                  "control parcial", "test parcial", "midterm",
                                  "intermediate"]):
        return "midterm_tests"

    # quiz
    if any(k in label for k in ["cuestionario", "quiz", "test corto",
                                  "prueba corta", "test de seguimiento"]):
        return "quizzes"

    # project / lab work
    if any(k in label for k in ["trabajo", "proyecto", "práctica", "practica",
                                  "prácticas", "practicas", "trabajo en grupo",
                                  "trabajo grupal", "proyecto grupal",
                                  "trabajo final", "informe", "memoria",
                                  "presentación", "presentacion",
                                  "project", "lab", "case"]):
        return "project"

    # participation
    if any(k in label for k in ["participación", "participacion", "asistencia",
                                  "participación activa", "participacion en clase",
                                  "participation"]):
        return "participation"

    return "other"


def extract_text_from_pdf(pdf_path: str) -> str:
    parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    parts.append(t)
    except Exception as e:
        print(f"  pdf read error {pdf_path}: {e}")
    return "\n".join(parts)


def fetch_html_text(url: str) -> str:
    try:
        import urllib3; urllib3.disable_warnings()
        resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        resp.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        return soup.get_text(separator="\n")
    except Exception as e:
        print(f"  html fetch error {url}: {e}")
        return ""


def is_likely_syllabus(text: str) -> bool:
    t = text.lower()
    return (
        any(m in t for m in EVAL_SECTION_MARKERS)
        and any(k in t for k in ["crédito", "credito", "credit", "asignatura",
                                   "course", "grado", "degree"])
    )


def find_eval_section(text: str) -> str:
    text_lower = text.lower()
    start = -1
    for marker in EVAL_SECTION_MARKERS:
        idx = text_lower.find(marker)
        if idx != -1:
            start = idx
            break

    if start == -1:
        return ""

    end_candidates = [text_lower.find(m, start + 10) for m in END_MARKERS]
    end_candidates = [x for x in end_candidates if x > start]

    end = min(end_candidates) if end_candidates else start + 3000
    return text[start:end]


def empty_grading() -> dict:
    return {
        "final_exam": 0,
        "midterm_tests": 0,
        "quizzes": 0,
        "project": 0,
        "participation": 0,
        "other": 0,
    }


def parse_grading_from_text(text: str) -> dict:
    grading = empty_grading()
    section = find_eval_section(text)
    if not section:
        return grading

    for line in section.splitlines():
        if "%" not in line:
            continue

        raw_label = None
        pct = None

        m = re.search(r"(.+?)\s+(\d{1,3})\s*%", line, flags=re.IGNORECASE)
        if m:
            raw_label = m.group(1).strip()
            pct = int(m.group(2))

        if raw_label is None:
            m2 = re.search(r"(.+?)[:\-]\s*(\d{1,3})\s*%", line, flags=re.IGNORECASE)
            if m2:
                raw_label = m2.group(1).strip()
                pct = int(m2.group(2))

        if raw_label is None or pct is None:
            continue

        category = map_label_es(raw_label)
        if category:
            grading[category] += pct

    return grading


def parse_grading_from_pdf_tables(pdf_path: str) -> dict:
    grading = empty_grading()

    try:
        with pdfplumber.open(pdf_path) as pdf:
            criteria_page = None
            for i, page in enumerate(pdf.pages):
                t = (page.extract_text() or "").lower()
                if any(m in t for m in EVAL_SECTION_MARKERS):
                    criteria_page = i
                    break

            if criteria_page is None:
                return grading

            for i in range(criteria_page, min(criteria_page + 4, len(pdf.pages))):
                tables = pdf.pages[i].extract_tables()
                for table in (tables or []):
                    for row in (table or []):
                        cleaned = [str(c).strip() if c else "" for c in row]
                        if len(cleaned) < 2:
                            continue
                        label = cleaned[0]
                        pct_cell = cleaned[1].lower()
                        m = re.search(r"(\d{1,3})\s*%", pct_cell)
                        if not m:
                            continue
                        pct = int(m.group(1))
                        category = map_label_es(label)
                        if category:
                            grading[category] += pct

    except Exception as e:
        print(f"  table extraction error {pdf_path}: {e}")

    return grading


def total_weight(grading: dict) -> int:
    return sum(grading.values())


def parse_syllabus(source: str, is_url: bool = False, is_html: bool = False) -> dict | None:
    """
    source: local file path or URL
    Returns grading dict or None if not a valid syllabus
    """
    if is_url and is_html:
        text = fetch_html_text(source)
    elif is_url:
        import tempfile, requests, urllib3; urllib3.disable_warnings()
        try:
            resp = requests.get(source, headers=HEADERS, timeout=20, verify=False)
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(resp.content)
                tmp_path = f.name
            text = extract_text_from_pdf(tmp_path)
            table_grading = parse_grading_from_pdf_tables(tmp_path)
            import os; os.unlink(tmp_path)
        except Exception as e:
            print(f"  download error {source}: {e}")
            return None
    else:
        text = extract_text_from_pdf(source)
        table_grading = parse_grading_from_pdf_tables(source)

    if not text or not is_likely_syllabus(text):
        return None

    text_grading = parse_grading_from_text(text)

    if is_html or (is_url and is_html):
        best = text_grading
    else:
        t_total = total_weight(table_grading)
        tx_total = total_weight(text_grading)
        if 90 <= t_total <= 110 and not (90 <= tx_total <= 110):
            best = table_grading
        elif 90 <= tx_total <= 110 and not (90 <= t_total <= 110):
            best = text_grading
        elif 90 <= t_total <= 110 and 90 <= tx_total <= 110:
            best = table_grading
        else:
            best = table_grading if abs(t_total - 100) <= abs(tx_total - 100) else text_grading

    return best
