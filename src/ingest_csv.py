"""Convert the PyThaiNLP Thai-law criminal CSV into normalized article records."""

import csv
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_DIR / "data" / "raw" / "penal_code_pythainlp.csv"
OUTPUT_PATH = PROJECT_DIR / "data" / "processed" / "pythainlp_articles.json"
SOURCE_URL = "https://github.com/PyThaiNLP/thai-law"
SOURCE_NAME = "pythainlp_thai_law"
LICENSE = "public domain"


def article_number(article_id):
    """Return the main article number when the id starts with digits."""
    match = re.match(r"^\s*(\d+)", article_id or "")
    return int(match.group(1)) if match else None


def ingest_csv(input_path=INPUT_PATH):
    records = []
    with Path(input_path).open("r", encoding="utf-8-sig", newline="") as file:
        for row_number, row in enumerate(csv.DictReader(file), start=2):
            article_id = (row.get("article") or "").strip()
            text = (row.get("text") or "").strip()
            if not article_id or not text or article_id.lower() == "null":
                continue
            records.append(
                {
                    "id": f"{SOURCE_NAME}_{article_id}",
                    "source": SOURCE_NAME,
                    "article_id": article_id,
                    "article_number": article_number(article_id),
                    "source_url": SOURCE_URL,
                    "license": LICENSE,
                    "notes": (row.get("notes") or "").strip(),
                    "csv_row": row_number,
                    "text": text,
                }
            )
    return records


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {INPUT_PATH}")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    records = ingest_csv()
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)
    print(f"Saved {len(records)} article records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
