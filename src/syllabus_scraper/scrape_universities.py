"""
Main multi-university scraper.
Loads config/universities.yaml, runs each university's scraper,
downloads syllabuses, parses grading, and saves to data/processed/multi_uni_links.csv
"""

import os
import time
import yaml
import requests
import pandas as pd

from syllabus_scraper.universities.ucm import UCMScraper
from syllabus_scraper.universities.uc3m import UC3MScraper
from syllabus_scraper.universities.uam import UAMScraper
from syllabus_scraper.parse_grading_es import parse_syllabus, total_weight

SCRAPERS = {
    "UCM": UCMScraper(),
    "UC3M": UC3MScraper(),
    "UAM": UAMScraper(),
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def load_config(path: str = "config/universities.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def scrape_links(config: dict, universities: list[str] | None = None) -> pd.DataFrame:
    rows = []
    for uni_key, uni_cfg in config["universities"].items():
        if uni_key == "IE":
            continue  # IE has its own Selenium pipeline
        if universities and uni_key not in universities:
            continue

        scraper = SCRAPERS.get(uni_key)
        if scraper is None:
            print(f"no scraper for {uni_key}, skipping")
            continue

        for prog_name, prog_cfg in uni_cfg["programs"].items():
            links = scraper.get_syllabus_links(prog_name, prog_cfg)
            for link in links:
                link["university_full"] = uni_cfg["name"]
            rows.extend(links)

    df = pd.DataFrame(rows)
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/multi_uni_links.csv", index=False)
    print(f"\nsaved {len(df)} links to data/processed/multi_uni_links.csv")
    return df


def download_and_parse(links_csv: str = "data/processed/multi_uni_links.csv") -> pd.DataFrame:
    df = pd.read_csv(links_csv)
    os.makedirs("data/raw_es", exist_ok=True)

    rows = []
    for _, row in df.iterrows():
        url = row["url"]
        university = row["university"]
        program = row["program"]
        program_type = row["program_type"]
        course_name = row.get("course_name", "")
        fmt = row.get("format", "pdf")

        print(f"  parsing [{university}] {course_name[:60]}")

        is_html = fmt == "html"
        grading = parse_syllabus(url, is_url=True, is_html=is_html)

        if grading is None:
            continue

        tw = total_weight(grading)
        status = "ok" if 90 <= tw <= 110 else "needs_review"

        rows.append({
            "university": university,
            "program": program,
            "program_type": program_type,
            "course_name": course_name,
            "url": url,
            "final_exam": grading["final_exam"],
            "midterm_tests": grading["midterm_tests"],
            "quizzes": grading["quizzes"],
            "project": grading["project"],
            "participation": grading["participation"],
            "other": grading["other"],
            "total_weight": tw,
            "parse_status": status,
        })

        time.sleep(0.5)

    result_df = pd.DataFrame(rows)
    result_df.to_csv("data/processed/multi_uni_grading.csv", index=False)
    print(f"\nsaved {len(result_df)} parsed courses to data/processed/multi_uni_grading.csv")
    return result_df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--universities", nargs="*", help="which universities to scrape (default: all)")
    parser.add_argument("--skip-scrape", action="store_true", help="skip scraping, use existing links CSV")
    args = parser.parse_args()

    config = load_config()

    if not args.skip_scrape:
        scrape_links(config, universities=args.universities)

    download_and_parse()
