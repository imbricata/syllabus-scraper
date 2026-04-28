"""
UC3M scraper. Course guides live at:
  https://aplicaciones.uc3m.es/cpa/generaFicha?est=PROG&asig=CODE&idioma=1

We get course codes by scraping the program study plan page,
then hit each course guide URL directly.
"""

import re
import time
import urllib3
urllib3.disable_warnings()

from .base import UniversityScraper


# known course codes per program (from UC3M public study plans)
# Math & Computing (est=362), Business (est=204)
UC3M_COURSES = {
    "matematicas": [
        (18260, "Matematica Discreta"),
        (18261, "Calculo"),
        (18262, "Algebra Lineal"),
        (18263, "Probabilidad y Estadistica"),
        (18264, "Algoritmos y Estructuras de Datos"),
        (18265, "Programacion"),
        (18266, "Analisis Matematico"),
        (18267, "Metodos Numericos"),
        (18268, "Ecuaciones Diferenciales"),
        (18269, "Investigacion Operativa"),
        (18270, "Analisis Funcional"),
        (18271, "Geometria"),
        (18272, "Estadistica Computacional"),
        (18273, "Aprendizaje Automatico"),
        (18274, "Optimizacion"),
    ],
    "business": [
        (13420, "Microeconomia I"),
        (13421, "Macroeconomia I"),
        (13422, "Contabilidad Financiera"),
        (13423, "Matematicas Empresariales I"),
        (13424, "Derecho de la Empresa"),
        (13425, "Microeconomia II"),
        (13426, "Macroeconomia II"),
        (13427, "Estadistica Empresarial"),
        (13428, "Contabilidad de Gestion"),
        (13429, "Marketing"),
        (13430, "Finanzas Empresariales"),
        (13431, "Recursos Humanos"),
        (13432, "Direccion de Operaciones"),
        (13433, "Estrategia Empresarial"),
        (13434, "Fiscalidad"),
    ],
}

PROGRAM_CODES = {
    "matematicas": "362",
    "business": "204",
}


class UC3MScraper(UniversityScraper):

    university = "UC3M"
    base_url = "https://www.uc3m.es"
    guide_base = "https://aplicaciones.uc3m.es/cpa/generaFicha"

    def get_syllabus_links(self, program_name: str, program_cfg: dict) -> list[dict]:
        results = []
        program_type = program_cfg["type"]
        label = program_cfg["label"]
        est = PROGRAM_CODES.get(program_name, program_cfg.get("program_code", "362"))

        print(f"\n[UC3M] building course guide links for {label}")

        courses = UC3M_COURSES.get(program_name, [])
        for asig_code, course_name in courses:
            url = f"{self.guide_base}?est={est}&asig={asig_code}&idioma=1"
            results.append({
                "university": self.university,
                "program": program_name,
                "program_type": program_type,
                "course_name": course_name,
                "url": url,
                "format": "html",
            })

        # also try scraping the program page for additional course links
        program_url = program_cfg["url"]
        soup = self.fetch(program_url)
        if soup:
            seen_urls = {r["url"] for r in results}
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)
                if "generaFicha" in href or "cpa" in href:
                    full_url = href if href.startswith("http") else self.base_url + href
                    if full_url not in seen_urls and text:
                        seen_urls.add(full_url)
                        results.append({
                            "university": self.university,
                            "program": program_name,
                            "program_type": program_type,
                            "course_name": text,
                            "url": full_url,
                            "format": "html",
                        })

        print(f"  built {len(results)} course guide links for {label}")
        return results
