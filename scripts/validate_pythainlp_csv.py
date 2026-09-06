"""Sanity-check article coverage and ordering in the PyThaiNLP CSV dataset."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "processed" / "pythainlp_articles.json"
REPORT_PATH = ROOT / "data" / "processed" / "pythainlp_validation_report.json"
ARTICLE_ID_RE = re.compile(r"^(\d+)(?:/(\d+))?$")
LARGE_GAP = 5


def validate(records):
    numeric = []
    non_article = []
    for record in records:
        article_id = str(record.get("article_id", "")).strip()
        match = ARTICLE_ID_RE.fullmatch(article_id)
        if match:
            numeric.append(
                {
                    "article_id": article_id,
                    "article_number": int(match.group(1)),
                    "sub_article": int(match.group(2)) if match.group(2) else None,
                    "record_id": record.get("id"),
                }
            )
        else:
            non_article.append(article_id)

    order_anomalies = []
    for previous, current in zip(numeric, numeric[1:]):
        if current["article_number"] < previous["article_number"]:
            order_anomalies.append({"previous": previous, "current": current})

    base_numbers = sorted({item["article_number"] for item in numeric})
    gaps = []
    for previous, current in zip(base_numbers, base_numbers[1:]):
        if current - previous > LARGE_GAP:
            gaps.append(
                {
                    "from": previous,
                    "to": current,
                    "gap": current - previous,
                    "missing_range": [previous + 1, current - 1],
                }
            )

    duplicate_ids = [
        {"article_id": article_id, "count": count}
        for article_id, count in Counter(item["article_id"] for item in numeric).items()
        if count > 1
    ]
    minimum = min(base_numbers) if base_numbers else None
    maximum = max(base_numbers) if base_numbers else None
    missing = (
        sorted(set(range(1, maximum + 1)) - set(base_numbers)) if maximum else []
    )

    return {
        "input_file": str(INPUT_PATH),
        "records": len(records),
        "numeric_article_records": len(numeric),
        "non_article_ids": non_article,
        "unique_base_article_numbers": len(base_numbers),
        "base_article_range": {"min": minimum, "max": maximum},
        "expected_approximation": "The Thai Criminal Code has approximately 400 base article numbers; this dataset reaches 398 and includes sub-articles.",
        "checks": {
            "out_of_order_count": len(order_anomalies),
            "duplicate_article_id_count": len(duplicate_ids),
            "large_gap_count": len(gaps),
            "large_gap_threshold": LARGE_GAP,
            "missing_base_numbers_1_to_max_count": len(missing),
        },
        "out_of_order": order_anomalies,
        "duplicate_article_ids": duplicate_ids,
        "large_gaps": gaps,
        "missing_base_numbers_1_to_max": missing,
    }


def main() -> int:
    if not INPUT_PATH.exists():
        print(f"ERROR: input not found: {INPUT_PATH}", file=sys.stderr)
        return 2
    with INPUT_PATH.open("r", encoding="utf-8") as file:
        records = json.load(file)
    report = validate(records)
    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print(f"Records: {report['records']}")
    print(f"Numeric article records: {report['numeric_article_records']}")
    print(f"Unique base articles: {report['unique_base_article_numbers']}")
    print(f"Base range: {report['base_article_range']}")
    print(f"Non-article IDs: {len(report['non_article_ids'])}")
    print(f"Out of order: {report['checks']['out_of_order_count']}")
    print(f"Duplicate article IDs: {report['checks']['duplicate_article_id_count']}")
    print(f"Large gaps > {LARGE_GAP}: {report['checks']['large_gap_count']}")
    print(f"Missing base numbers 1..max: {report['checks']['missing_base_numbers_1_to_max_count']}")
    print(f"Report saved: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
