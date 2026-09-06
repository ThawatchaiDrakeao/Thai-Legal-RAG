"""Validate OCR output for Thai article-number continuity.

This is a read-only diagnostic for OCR pages. It does not modify the source
JSON, chunks, embeddings, or FAISS index.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "processed" / "pdf_pages.json"
REPORT_PATH = ROOT / "data" / "processed" / "ocr_validation_report.json"
OCR_SOURCE = "penal_code_snapshot.pdf"
CONTEXT_RADIUS = 90

ARTICLE_RE = re.compile(
    r"มาตรา\s*([0-9๐-๙]+)\s*(ทวิ|ตรี|จัตวา)?",
    re.UNICODE,
)
THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")


def normalize_number(raw_number: str) -> int:
    """Convert Thai or Arabic digits to an integer."""
    return int(raw_number.translate(THAI_DIGITS))


def context_around(text: str, start: int, end: int) -> str:
    left = max(0, start - CONTEXT_RADIUS)
    right = min(len(text), end + CONTEXT_RADIUS)
    return " ".join(text[left:right].split())


def load_ocr_pages() -> list[dict]:
    with INPUT_PATH.open("r", encoding="utf-8") as file:
        records = json.load(file)
    return [
        record
        for record in records
        if record.get("extraction_method") == "ocr"
        and record.get("source_file") == OCR_SOURCE
    ]


def collect_occurrences(pages: list[dict]) -> list[dict]:
    occurrences = []
    for page in sorted(pages, key=lambda item: item.get("page_number", 0)):
        text = page.get("text", "")
        for match in ARTICLE_RE.finditer(text):
            suffix = match.group(2) or ""
            occurrences.append(
                {
                    "article_number": normalize_number(match.group(1)),
                    "raw_number": match.group(1),
                    "suffix": suffix,
                    "page_number": page.get("page_number"),
                    "source_file": page.get("source_file"),
                    "context": context_around(text, match.start(), match.end()),
                }
            )
    return occurrences


def non_decreasing_anomalies(occurrences: list[dict]) -> list[dict]:
    anomalies = []
    previous = None
    for current in occurrences:
        if previous is not None and current["article_number"] < previous["article_number"]:
            anomalies.append(
                {
                    "type": "out_of_order",
                    "previous": previous,
                    "current": current,
                }
            )
        previous = current
    return anomalies


def duplicate_groups(occurrences: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for occurrence in occurrences:
        # Article suffixes such as ทวิ/ตรี are separate legal article forms.
        key = (occurrence["article_number"], occurrence["suffix"])
        grouped[key].append(occurrence)

    duplicates = []
    for (article_number, suffix), matches in sorted(grouped.items()):
        if len(matches) < 2:
            continue
        duplicates.append(
            {
                "type": "duplicate_article_number",
                "article_number": article_number,
                "suffix": suffix,
                "count": len(matches),
                "occurrences": matches,
                "note": "May be a normal cross-reference; inspect contexts before treating as OCR error.",
            }
        )
    return duplicates


def gap_anomalies(occurrences: list[dict], minimum_gap: int = 5) -> list[dict]:
    anomalies = []
    for previous, current in zip(occurrences, occurrences[1:]):
        gap = current["article_number"] - previous["article_number"]
        if gap > minimum_gap:
            anomalies.append(
                {
                    "type": "large_article_gap",
                    "gap": gap,
                    "missing_range": [previous["article_number"] + 1, current["article_number"] - 1],
                    "previous": previous,
                    "current": current,
                }
            )
    return anomalies


def build_report(pages: list[dict], occurrences: list[dict]) -> dict:
    anomalies = (
        non_decreasing_anomalies(occurrences)
        + duplicate_groups(occurrences)
        + gap_anomalies(occurrences)
    )
    return {
        "input_file": str(INPUT_PATH),
        "source_file": OCR_SOURCE,
        "extraction_method": "ocr",
        "ocr_pages": len(pages),
        "article_occurrences": len(occurrences),
        "unique_article_numbers": len({item["article_number"] for item in occurrences}),
        "checks": {
            "out_of_order_count": sum(item["type"] == "out_of_order" for item in anomalies),
            "duplicate_group_count": sum(item["type"] == "duplicate_article_number" for item in anomalies),
            "large_gap_count": sum(item["type"] == "large_article_gap" for item in anomalies),
            "large_gap_threshold": 5,
        },
        "suspicious": anomalies,
    }


def print_summary(report: dict) -> None:
    print(f"OCR pages checked: {report['ocr_pages']}")
    print(f"Article occurrences: {report['article_occurrences']}")
    print(f"Unique article numbers: {report['unique_article_numbers']}")
    print("Suspicious findings:")
    for finding in report["suspicious"]:
        kind = finding["type"]
        if kind == "out_of_order":
            print(
                f"- OUT_OF_ORDER: page {finding['previous']['page_number']} "
                f"มาตรา {finding['previous']['article_number']} -> page {finding['current']['page_number']} "
                f"มาตรา {finding['current']['article_number']}\n"
                f"  context: {finding['current']['context']}"
            )
        elif kind == "duplicate_article_number":
            pages = [item["page_number"] for item in finding["occurrences"]]
            print(
                f"- DUPLICATE: มาตรา {finding['article_number']}{finding['suffix']} "
                f"พบ {finding['count']} ครั้ง หน้า {pages}"
            )
            for item in finding["occurrences"]:
                print(f"  page {item['page_number']}: {item['context']}")
        elif kind == "large_article_gap":
            print(
                f"- LARGE GAP: {finding['previous']['article_number']} -> "
                f"{finding['current']['article_number']} (gap {finding['gap']}) "
                f"หน้า {finding['previous']['page_number']} -> {finding['current']['page_number']}\n"
                f"  context: {finding['current']['context']}"
            )


def main() -> int:
    if not INPUT_PATH.exists():
        print(f"ERROR: input not found: {INPUT_PATH}", file=sys.stderr)
        return 2

    pages = load_ocr_pages()
    occurrences = collect_occurrences(pages)
    report = build_report(pages, occurrences)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print_summary(report)
    print(f"Report saved: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
