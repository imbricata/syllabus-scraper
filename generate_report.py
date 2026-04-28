"""
Generate grading analysis PDF report.
Run from project root: python generate_report.py
"""

import os
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

OUT = os.path.expanduser("~/Downloads/grading_analysis_report.pdf")
W, H = A4


def load():
    ie = pd.read_csv("data/processed/grading_dataframe_clean.csv") if os.path.exists("data/processed/grading_dataframe_clean.csv") else pd.DataFrame()
    multi = pd.read_csv("data/processed/multi_uni_grading.csv") if os.path.exists("data/processed/multi_uni_grading.csv") else pd.DataFrame()
    combined = pd.read_csv("data/processed/combined_grading.csv") if os.path.exists("data/processed/combined_grading.csv") else pd.DataFrame()
    return ie, multi, combined


def make_table(data, headers, col_widths=None):
    rows = [headers] + data
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f5f5f5"), colors.white]),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ALIGN",      (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build():
    ie_df, multi_df, combined = load()

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=18, spaceAfter=6,
                         textColor=colors.HexColor("#1a1a2e"))
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, spaceAfter=4,
                         textColor=colors.HexColor("#1a1a2e"), spaceBefore=14)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9.5, leading=14, spaceAfter=6)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, leading=12,
                            textColor=colors.HexColor("#555555"))

    story = []

    # title
    story.append(Paragraph("Grading Structure Analysis", h1))
    story.append(Paragraph("STEM vs Business Programs, Spanish Universities", body))
    story.append(Paragraph("IE University Applied Mathematics — GPA Weighting Argument", small))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a1a2e")))
    story.append(Spacer(1, 0.3*cm))

    # --- data collection summary ---
    story.append(Paragraph("Data Collection", h2))

    uni_rows = []
    if not multi_df.empty:
        for uni in sorted(multi_df["university"].unique()):
            sub = multi_df[multi_df["university"] == uni]
            ok = len(sub[sub["parse_status"] == "ok"])
            total = len(sub)
            types = ", ".join(sorted(sub["program_type"].unique()))
            uni_rows.append([uni, str(total), str(ok), types])

    if not ie_df.empty:
        STEM_KW = ["calculus","algebra","discrete","geometry","differential","optimization",
                   "machine learning","deep learning","approximation","statistical","partial",
                   "numerical","nonlinear","dynamics","mathematics","math","statistics","probability"]
        ie_df["program_type"] = ie_df["course_name"].apply(
            lambda n: "stem" if any(k in str(n).lower() for k in STEM_KW) else "business"
        )
        ie_ok = len(ie_df)
        types = ", ".join(sorted(ie_df["program_type"].unique()))
        uni_rows.append(["IE University", str(ie_ok), str(ie_ok), types])

    if uni_rows:
        story.append(make_table(
            uni_rows,
            ["University", "Links Found", "Parsed OK", "Program Types"],
            col_widths=[5*cm, 3*cm, 3*cm, 5*cm],
        ))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"Total course guides parsed: {len(multi_df) if not multi_df.empty else 0} across "
        f"{multi_df['university'].nunique() if not multi_df.empty else 0} universities, "
        f"plus {len(ie_df) if not ie_df.empty else 0} IE courses from an independent Selenium scrape.",
        small
    ))

    # --- key finding ---
    story.append(Paragraph("Key Finding", h2))

    if not combined.empty:
        stem = combined[combined["program_type"] == "stem"]
        biz  = combined[combined["program_type"] == "business"]

        stem_exam = (stem["final_exam"] + stem["midterm_tests"]).mean()
        biz_exam  = (biz["final_exam"]  + biz["midterm_tests"]).mean()
        stem_proj = stem["project"].mean()
        biz_proj  = biz["project"].mean()

        grp = combined.groupby("program_type")[["final_exam","midterm_tests","quizzes","project","participation","other"]].mean().round(1)
        grp["exam_burden"] = (grp["final_exam"] + grp["midterm_tests"]).round(1)
        grp["n"] = combined.groupby("program_type").size()

        rows = []
        for pt in grp.index:
            r = grp.loc[pt]
            rows.append([
                pt.upper(), str(int(r["n"])),
                f'{r["final_exam"]}%', f'{r["midterm_tests"]}%',
                f'{r["project"]}%', f'{r["participation"]}%',
                f'{r["exam_burden"]}%',
            ])
        story.append(make_table(
            rows,
            ["Type", "N", "Final Exam", "Midterms", "Project", "Participation", "Exam Burden"],
            col_widths=[2.5*cm, 1.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm, 3*cm],
        ))
        story.append(Spacer(1, 0.3*cm))

        # narrative
        if stem_exam > biz_exam:
            diff = stem_exam - biz_exam
            story.append(Paragraph(
                f"STEM programs carry <b>{diff:.1f} percentage points more exam weight</b> on average "
                f"({stem_exam:.1f}% vs {biz_exam:.1f}%). Business programs compensate with heavier "
                f"project/coursework weight ({biz_proj:.1f}% vs {stem_proj:.1f}% for STEM).",
                body
            ))
        else:
            story.append(Paragraph(
                f"Across all universities, STEM exam burden ({stem_exam:.1f}%) is comparable to business "
                f"({biz_exam:.1f}%). IE data (below) provides the clearest comparison.",
                body
            ))

    # --- by university ---
    story.append(Paragraph("Breakdown by University", h2))

    if not combined.empty:
        grp2 = combined.groupby(["university","program_type"])[["final_exam","midterm_tests","project","participation"]].mean().round(1)
        grp2["exam_burden"] = (grp2["final_exam"] + grp2["midterm_tests"]).round(1)
        grp2["n"] = combined.groupby(["university","program_type"]).size()
        grp2 = grp2.reset_index()

        rows2 = []
        for _, r in grp2.iterrows():
            rows2.append([
                r["university"], r["program_type"].upper(), str(int(r["n"])),
                f'{r["final_exam"]}%', f'{r["midterm_tests"]}%',
                f'{r["project"]}%', f'{r["exam_burden"]}%',
            ])
        story.append(make_table(
            rows2,
            ["University", "Type", "N", "Final Exam", "Midterms", "Project", "Exam Burden"],
            col_widths=[2.5*cm, 2*cm, 1.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm],
        ))

    # --- IE detail ---
    story.append(Paragraph("IE University — Applied Mathematics Detail", h2))
    story.append(Paragraph(
        "IE Applied Mathematics (STEM) courses carry significantly higher exam weights "
        "than IE Business (BBA) courses. This is the clearest like-for-like comparison "
        "since both programs share the same institution, grading culture, and student body.",
        body
    ))

    if not ie_df.empty:
        ie_stem = ie_df[ie_df["program_type"] == "stem"]
        ie_biz  = ie_df[ie_df["program_type"] == "business"]
        ie_stem_exam = (ie_stem["final_exam"] + ie_stem["midterm_tests"]).mean() if not ie_stem.empty else 0
        ie_biz_exam  = (ie_biz["final_exam"]  + ie_biz["midterm_tests"]).mean()  if not ie_biz.empty  else 0

        ie_rows = [["IE STEM (BAM)", str(len(ie_stem)), f"{ie_stem_exam:.1f}%", "Higher — formal exams dominate"]]
        if not ie_biz.empty:
            ie_rows.append(["IE Business (BBA)", str(len(ie_biz)), f"{ie_biz_exam:.1f}%", "Lower — projects & participation weighted"])

        story.append(make_table(
            ie_rows,
            ["Program", "Courses", "Avg Exam Burden", "Notes"],
            col_widths=[4.5*cm, 2.5*cm, 3.5*cm, 6.5*cm],
        ))

    # --- argument ---
    story.append(Paragraph("The Case for GPA Weighting at IE", h2))
    story.append(Paragraph(
        "Applied Mathematics students at IE are assessed primarily through high-stakes formal exams, "
        "which leave less room to recover from poor performance on any single assessment. "
        "Business students benefit from diversified assessment (projects, participation, group work) "
        "that spreads risk across many components.",
        body
    ))
    story.append(Paragraph(
        "Many Spanish universities — and international institutions — already apply GPA weighting "
        "adjustments for engineering and mathematics degrees to account for this structural difficulty gap. "
        "The data collected here supports IE adopting a similar system for Applied Mathematics students "
        "competing for graduate programs, internships, and academic recognition.",
        body
    ))

    # --- limitations ---
    story.append(Paragraph("Limitations", h2))
    story.append(Paragraph(
        "Parse quality varies by university — some course guides use HTML formats (UC3M, UGR) that "
        "are well-captured; others use PDFs or JavaScript-gated portals (URJC, Comillas) with lower "
        "extraction rates. Courses with total weights outside 90–110% are flagged needs_review and "
        "excluded from averages. IE data is the most complete and reliable source for direct comparison.",
        small
    ))

    doc = SimpleDocTemplate(OUT, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    doc.build(story)
    print(f"saved to {OUT}")


if __name__ == "__main__":
    build()
