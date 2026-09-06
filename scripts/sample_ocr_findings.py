"""Sample OCR validation findings for manual review.

The sampling is deterministic and does not modify the validation report.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "data" / "processed" / "ocr_validation_report.json"
OUTPUT_PATH = ROOT / "data" / "processed" / "ocr_sample_for_review.txt"
SAMPLE_SIZE = 8
RANDOM_SEED = 42

GROUPS = (
    ("out_of_order", "out_of_order"),
    ("duplicate", "duplicate_article_number"),
    ("large_gap", "large_article_gap"),
)


def load_findings() -> list[dict]:
    with REPORT_PATH.open("r", encoding="utf-8") as file:
        report = json.load(file)
    return report.get("suspicious", [])


def group_findings(findings: list[dict]) -> dict[str, list[dict]]:
    return {
        label: [finding for finding in findings if finding.get("type") == report_type]
        for label, report_type in GROUPS
    }


def context_line(item: dict) -> str:
    return f"หน้า {item.get('page_number')}: {item.get('context', '').strip()}"


def format_finding(group: str, finding: dict, number: int) -> str:
    lines = [f"[{group}] รายการที่ {number}", f"ประเภทปัญหา: {finding.get('type')}" ]

    if group == "out_of_order":
        previous = finding["previous"]
        current = finding["current"]
        lines.extend(
            [
                f"เลขมาตรา: {previous['article_number']} -> {current['article_number']}",
                f"หน้า: {previous['page_number']} -> {current['page_number']}",
                f"Context ก่อนหน้า: {context_line(previous)}",
                f"Context ปัจจุบัน: {context_line(current)}",
            ]
        )
    elif group == "large_gap":
        previous = finding["previous"]
        current = finding["current"]
        lines.extend(
            [
                f"เลขมาตรา: {previous['article_number']} -> {current['article_number']}",
                f"Gap: {finding['gap']} (ช่วงที่อาจหาย: {finding['missing_range'][0]} - {finding['missing_range'][1]})",
                f"หน้า: {previous['page_number']} -> {current['page_number']}",
                f"Context ก่อนหน้า: {context_line(previous)}",
                f"Context ปัจจุบัน: {context_line(current)}",
            ]
        )
    else:
        lines.extend(
            [
                f"เลขมาตรา: {finding['article_number']}{finding.get('suffix', '')}",
                f"จำนวนที่พบ: {finding['count']}",
                "รายการที่พบ:",
            ]
        )
        lines.extend(f"  - {context_line(item)}" for item in finding["occurrences"])

    return "\n".join(lines)


def build_sample_text(findings: list[dict]) -> str:
    rng = random.Random(RANDOM_SEED)
    grouped = group_findings(findings)
    sections = [
        "Thai Legal RAG - OCR Findings Manual Review Sample",
        f"Random seed: {RANDOM_SEED}",
        f"Sample size per group: {SAMPLE_SIZE}",
        "หมายเหตุ: context ถูกเก็บจากรายงาน validation รอบคำว่า มาตรา เพื่อใช้ตรวจด้วยตา",
        "",
    ]

    for group, _ in GROUPS:
        candidates = grouped[group]
        selected = rng.sample(candidates, min(SAMPLE_SIZE, len(candidates)))
        sections.append(f"{'=' * 80}\nกลุ่ม: {group} ({len(selected)}/{len(candidates)} รายการ)\n{'=' * 80}")
        for index, finding in enumerate(selected, start=1):
            sections.append(format_finding(group, finding, index))
            sections.append("-" * 80)

    return "\n".join(sections).rstrip() + "\n"


def main() -> int:
    if not REPORT_PATH.exists():
        print(f"ERROR: report not found: {REPORT_PATH}", file=sys.stderr)
        return 2

    output = build_sample_text(load_findings())
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    print(output, end="")
    print(f"Saved review sample: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
