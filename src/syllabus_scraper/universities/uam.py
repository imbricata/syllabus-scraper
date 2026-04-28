"""
UAM scraper. Course guides live at the virtual secretariat:
  https://secretaria-virtual.uam.es/doa/consultaPublica/look[conpub]MostrarPubGuiaDocAs
  ?_anoAcademico=2025&_codAsignatura=CODE&entradaPublica=true&idiomaPais=es.ES

We use known subject codes from the public study plans.
"""

import time
import urllib3
urllib3.disable_warnings()

from .base import UniversityScraper


# known subject codes for UAM programs (from public study plans)
UAM_COURSES = {
    "matematicas": [
        (16473, "Variable Real"),
        (16474, "Calculo Diferencial"),
        (16475, "Algebra Lineal"),
        (16476, "Topologia"),
        (16477, "Analisis Matematico"),
        (16478, "Geometria"),
        (16479, "Probabilidad"),
        (16480, "Estadistica"),
        (16481, "Ecuaciones Diferenciales"),
        (16482, "Analisis Numerico"),
        (16483, "Algebra Abstracta"),
        (16484, "Analisis Funcional"),
        (16485, "Optimizacion"),
        (16486, "Teoria de Numeros"),
        (16487, "Matematica Discreta"),
    ],
    "ade": [
        (20401, "Introduccion a la Economia"),
        (20402, "Matematicas para la Empresa I"),
        (20403, "Contabilidad Financiera"),
        (20404, "Microeconomia"),
        (20405, "Derecho Mercantil"),
        (20406, "Matematicas para la Empresa II"),
        (20407, "Macroeconomia"),
        (20408, "Estadistica Empresarial"),
        (20409, "Contabilidad de Costes"),
        (20410, "Marketing"),
        (20411, "Finanzas"),
        (20412, "Recursos Humanos"),
        (20413, "Operaciones"),
        (20414, "Estrategia"),
        (20415, "Fiscalidad de la Empresa"),
    ],
}

GUIDE_BASE = (
    "https://secretaria-virtual.uam.es/doa/consultaPublica/"
    "look[conpub]MostrarPubGuiaDocAs"
    "?_anoAcademico=2025&_codAsignatura={code}"
    "&entradaPublica=true&idiomaPais=es.ES"
)


class UAMScraper(UniversityScraper):

    university = "UAM"
    base_url = "https://www.uam.es"

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        results = []
        program_type = program_cfg["type"]
        label = program_cfg["label"]

        print(f"\n[UAM] building course guide links for {label}")

        courses = UAM_COURSES.get(program_name, [])
        for code, course_name in courses:
            url = GUIDE_BASE.format(code=code)
            results.append({
                "university": self.university,
                "program": program_name,
                "program_type": program_type,
                "course_name": course_name,
                "url": url,
                "format": "html",
            })

        # also try scraping the program page for any directly linked guides
        program_url = program_cfg["url"]
        soup = self.fetch(program_url)
        if soup:
            seen_urls = {r["url"] for r in results}
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)
                if "secretaria-virtual" in href or href.endswith(".pdf"):
                    full_url = href if href.startswith("http") else self.base_url + href
                    if full_url not in seen_urls and text:
                        seen_urls.add(full_url)
                        results.append({
                            "university": self.university,
                            "program": program_name,
                            "program_type": program_type,
                            "course_name": text,
                            "url": full_url,
                            "format": "pdf" if href.endswith(".pdf") else "html",
                        })

        print(f"  built {len(results)} course guide links for {label}")
        return results
