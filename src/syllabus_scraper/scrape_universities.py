"""
Main multi-university scraper.
Loads config/universities.yaml, runs each university's scraper,
downloads syllabuses, parses grading, and saves to data/processed/multi_uni_grading.csv
"""

import os
import time
import yaml
import requests
import pandas as pd

from syllabus_scraper.universities.ucm import UCMScraper
from syllabus_scraper.universities.uc3m import UC3MScraper
from syllabus_scraper.universities.uam import UAMScraper
from syllabus_scraper.universities.ugr import UGRScraper
from syllabus_scraper.universities.urjc import URJCScraper
from syllabus_scraper.universities.comillas import ComillasScraper
from syllabus_scraper.universities.ub import UBScraper
from syllabus_scraper.universities.unav import UNAVScraper
from syllabus_scraper.parse_grading_es import parse_syllabus, total_weight

SCRAPERS = {
    "UCM": UCMScraper(),
    "UC3M": UC3MScraper(),
    "UAM": UAMScraper(),
    "UGR": UGRScraper(),
    "URJC": URJCScraper(),
    "Comillas": ComillasScraper(),
    "UB": UBScraper(),
    "UNAV": UNAVScraper(),
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
            continue
        if universities and uni_key not in universities:
            continue

        scraper = SCRAPERS.get(uni_key)
        if scraper is None:
            print(f"[SKIP] no scraper registered for {uni_key}")
            continue

        for prog_name, prog_cfg in uni_cfg["programs"].items():
            links = scraper.get_syllabus_links(prog_name, prog_cfg)
            for link in links:
                link["university_full"] = uni_cfg["name"]
            rows.extend(links)
            print(f"  -> {uni_key}/{prog_name}: {len(links)} links collected")

    df = pd.DataFrame(rows)
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/multi_uni_links.csv", index=False)
    print(f"\ntotal: {len(df)} links saved to data/processed/multi_uni_links.csv")
    return df


def download_and_parse(links_csv: str = "data/processed/multi_uni_links.csv") -> pd.DataFrame:
    df = pd.read_csv(links_csv)
    os.makedirs("data/raw_es", exist_ok=True)

    total = len(df)
    rows = []
    ok_count = 0
    review_count = 0
    skip_count = 0

    print(f"\nparsing {total} course guides...")

    for i, row in df.iterrows():
        url = row["url"]
        university = row["university"]
        program = row["program"]
        program_type = row["program_type"]
        course_name = row.get("course_name", "")
        fmt = row.get("format", "pdf")

        print(f"  [{i+1}/{total}] [{university}] {str(course_name)[:55]}")

        is_html = fmt == "html"
        grading = parse_syllabus(url, is_url=True, is_html=is_html)

        if grading is None:
            skip_count += 1
            continue

        tw = total_weight(grading)
        if 90 <= tw <= 110:
            status = "ok"
            ok_count += 1
        else:
            status = "needs_review"
            review_count += 1

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

        time.sleep(0.4)

    result_df = pd.DataFrame(rows)
    result_df.to_csv("data/processed/multi_uni_grading.csv", index=False)

    print(f"\nparse summary:")
    print(f"  ok:           {ok_count}")
    print(f"  needs_review: {review_count}")
    print(f"  skipped:      {skip_count}")
    print(f"  saved {len(result_df)} courses to data/processed/multi_uni_grading.csv")

    return result_df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--universities", nargs="*", help="universities to scrape (default: all)")
    parser.add_argument("--skip-scrape", action="store_true", help="skip link discovery, use existing CSV")
    parser.add_argument("--links-only", action="store_true", help="only discover links, skip parsing")
    args = parser.parse_args()

    config = load_config()

    if not args.skip_scrape:
        scrape_links(config, universities=args.universities)

    if not args.links_only:
        download_and_parse()
