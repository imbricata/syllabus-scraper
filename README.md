# syllabus-scraper

Scrapes, downloads, and parses grading breakdowns from university course syllabuses across multiple Spanish universities, then compares STEM vs business assessment structures.

The goal is to build evidence that harder bachelor programs (applied mathematics, engineering) carry significantly higher exam burdens than business programs, supporting the case for a GPA weighting system at IE University.

## Universities covered

| University | Programs |
|---|---|
| IE University | Applied Mathematics (STEM), BBA (Business) |
| UCM | Matemáticas (STEM), ADE (Business) |
| UC3M | Applied Mathematics (STEM), Business Administration (Business) |
| UAM | Matemáticas (STEM), ADE (Business) |

## Install

```bash
pip install -e .
```

## Pipeline

### IE University (original pipeline)

```bash
python -m syllabus_scraper.scrape_syllabus_selenium  # scrape IE syllabus links
python -m syllabus_scraper.filter_syllabus_links      # filter candidates
python -m syllabus_scraper.download_pdfs              # download PDFs
python -m syllabus_scraper.extract_text               # verify PDFs are syllabuses
python -m syllabus_scraper.parse_grading              # extract grading weights
```

### Other Spanish universities

```bash
# scrape and parse all universities
python -m syllabus_scraper.scrape_universities

# scrape specific universities only
python -m syllabus_scraper.scrape_universities --universities UCM UC3M

# skip scraping, re-parse from existing links CSV
python -m syllabus_scraper.scrape_universities --skip-scrape
```

### Analysis

```bash
python -m syllabus_scraper.analysis.compare
```

Prints a comparison table (STEM vs business) and the key stats for the weighting argument.

## Output files

All outputs land in `data/processed/`:

| File | Description |
|---|---|
| `grading_dataframe_clean.csv` | IE grading data, clean rows only |
| `multi_uni_links.csv` | syllabus links collected from other universities |
| `multi_uni_grading.csv` | parsed grading data from other universities |
| `combined_grading.csv` | IE + all other universities merged |

## Config

`config/universities.yaml` defines which universities and programs to scrape. Add new universities there and implement a matching scraper in `src/syllabus_scraper/universities/`.

## Tests

```bash
pytest tests/
```
