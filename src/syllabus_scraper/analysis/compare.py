"""
Compares grading structures across universities and program types.
The goal: show that STEM programs (math, engineering) use harder
assessment structures than business programs, supporting the case
for a GPA weighting system at IE.

Run: python -m syllabus_scraper.analysis.compare
"""

import os
import pandas as pd
import warnings
warnings.filterwarnings("ignore")


GRADING_COLS = ["final_exam", "midterm_tests", "quizzes", "project", "participation", "other"]


def load_data() -> pd.DataFrame:
    frames = []

    # IE data from existing pipeline
    ie_path = "data/processed/grading_dataframe_clean.csv"
    if os.path.exists(ie_path):
        ie = pd.read_csv(ie_path)
        ie["university"] = "IE"
        # IE only has one program type in clean data, we tag it based on filename
        # BAM courses are STEM, BBA courses are business
        ie["program_type"] = ie["filename"].apply(
            lambda f: "stem" if any(k in f.lower() for k in ["math", "bam", "calculus", "algebra", "statistics", "linear", "differential"]) else "business"
        )
        ie["program"] = ie["program_type"].apply(lambda t: "applied_mathematics" if t == "stem" else "bba")
        frames.append(ie[["university", "program", "program_type", "course_name"] + GRADING_COLS])

    # multi-university data
    multi_path = "data/processed/multi_uni_grading.csv"
    if os.path.exists(multi_path):
        multi = pd.read_csv(multi_path)
        multi = multi[multi["parse_status"] == "ok"]
        frames.append(multi[["university", "program", "program_type", "course_name"] + GRADING_COLS])

    if not frames:
        print("no data found, run the scraper pipelines first")
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    return df


def summarize_by_program_type(df: pd.DataFrame) -> pd.DataFrame:
    """avg grading weights broken down by stem vs business"""
    summary = (
        df.groupby("program_type")[GRADING_COLS]
        .mean()
        .round(1)
    )
    summary["exam_burden"] = summary["final_exam"] + summary["midterm_tests"]
    summary["n_courses"] = df.groupby("program_type").size()
    return summary


def summarize_by_university_and_type(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["university", "program_type"])[GRADING_COLS]
        .mean()
        .round(1)
    )
    summary["exam_burden"] = summary["final_exam"] + summary["midterm_tests"]
    summary["n_courses"] = df.groupby(["university", "program_type"]).size()
    return summary


def print_weighting_argument(df: pd.DataFrame):
    """prints the key stats to support the weighting argument"""
    stem = df[df["program_type"] == "stem"]
    biz = df[df["program_type"] == "business"]

    if stem.empty or biz.empty:
        print("need both stem and business data to compare")
        return

    stem_exam = (stem["final_exam"] + stem["midterm_tests"]).mean()
    biz_exam = (biz["final_exam"] + biz["midterm_tests"]).mean()
    stem_proj = stem["project"].mean()
    biz_proj = biz["project"].mean()
    stem_part = stem["participation"].mean()
    biz_part = biz["participation"].mean()

    print("\n" + "=" * 60)
    print("GRADING STRUCTURE COMPARISON: STEM vs BUSINESS")
    print("=" * 60)
    print(f"\n  courses analyzed: {len(stem)} STEM, {len(biz)} business")
    print(f"\n  avg exam burden (final + midterm):")
    print(f"    STEM:     {stem_exam:.1f}%")
    print(f"    Business: {biz_exam:.1f}%")
    print(f"    diff:     +{stem_exam - biz_exam:.1f}pp in STEM")
    print(f"\n  avg project/coursework weight:")
    print(f"    STEM:     {stem_proj:.1f}%")
    print(f"    Business: {biz_proj:.1f}%")
    print(f"\n  avg participation weight:")
    print(f"    STEM:     {stem_part:.1f}%")
    print(f"    Business: {biz_part:.1f}%")
    print()

    if stem_exam > biz_exam:
        print(f"  STEM programs carry {stem_exam - biz_exam:.1f}pp more exam weight on average.")
        print("  This supports the case for a GPA weighting adjustment at IE,")
        print("  where Applied Mathematics students face harder formal assessment.")
    print("=" * 60)


def main():
    df = load_data()
    if df.empty:
        return

    print(f"\nloaded {len(df)} courses total")
    print(f"universities: {sorted(df['university'].unique())}")
    print(f"program types: {sorted(df['program_type'].unique())}")

    print("\n--- by program type ---")
    print(summarize_by_program_type(df).to_string())

    print("\n--- by university + program type ---")
    print(summarize_by_university_and_type(df).to_string())

    print_weighting_argument(df)

    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/combined_grading.csv", index=False)
    print("\nsaved combined dataset to data/processed/combined_grading.csv")


if __name__ == "__main__":
    main()
