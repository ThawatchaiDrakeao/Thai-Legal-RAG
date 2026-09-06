"""Compare Thai PDF text extraction on one page.

Run from the project root, for example:
    python scripts/compare_pdf_extract.py --page 108

The PDF is copied to an ASCII-only temporary path so native PDF libraries do
not fail merely because the project directory contains Thai characters.
This diagnostic does not modify source PDFs or processed/index files.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "data" / "raw" / "penal_code_snapshot.pdf"


def count_bad_glyphs(text: str) -> dict[str, int]:
    private_use = [
        char
        for char in text
        if any(
            start <= ord(char) <= end
            for start, end in ((0xE000, 0xF8FF), (0xF0000, 0xFFFFD), (0x100000, 0x10FFFD))
        )
    ]
    return {
        "replacement_character": text.count("\ufffd"),
        "square_glyph": text.count("□"),
        "private_use_characters": len(private_use),
        "private_use_codepoints": sorted({f"U+{ord(char):04X}" for char in private_use}),
        "thai_characters": sum("\u0e00" <= char <= "\u0e7f" for char in text),
        "characters": len(text),
    }


def extract_with_pypdf(pdf_path: Path, page_index: int) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    return reader.pages[page_index].extract_text() or ""


def extract_with_pdfplumber(pdf_path: Path, page_index: int) -> str:
    import pdfplumber

    with pdfplumber.open(str(pdf_path)) as pdf:
        return pdf.pages[page_index].extract_text() or ""


def extract_with_pymupdf(pdf_path: Path, page_index: int) -> str:
    import fitz

    document = fitz.open(str(pdf_path))
    try:
        return document[page_index].get_text("text") or ""
    finally:
        document.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pdf",
        type=Path,
        default=DEFAULT_PDF,
        help="PDF path (default: penal_code_snapshot.pdf)",
    )
    parser.add_argument(
        "--page",
        type=int,
        default=108,
        help="1-based page number (default: 108)",
    )
    args = parser.parse_args()

    pdf_path = args.pdf if args.pdf.is_absolute() else ROOT / args.pdf
    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}", file=sys.stderr)
        return 2
    if args.page < 1:
        print("ERROR: --page must be >= 1", file=sys.stderr)
        return 2

    sys.stdout.reconfigure(encoding="utf-8")
    page_index = args.page - 1

    # Use an ASCII temp filename for fitz and any other native file handling.
    with tempfile.TemporaryDirectory(prefix="thai_pdf_compare_") as temp_dir:
        ascii_pdf = Path(temp_dir) / "input.pdf"
        shutil.copy2(pdf_path, ascii_pdf)

        methods = (
            ("pypdf", extract_with_pypdf, pdf_path),
            ("pdfplumber", extract_with_pdfplumber, pdf_path),
            ("PyMuPDF (fitz)", extract_with_pymupdf, ascii_pdf),
        )

        print(f"PDF: {pdf_path}")
        print(f"PAGE: {args.page} (1-based)")
        print("=" * 80)

        for name, extractor, input_path in methods:
            print(f"\n### {name} ###")
            try:
                text = extractor(input_path, page_index)
            except Exception as exc:  # Keep the other comparisons running.
                print(f"ERROR: {type(exc).__name__}: {exc}")
                continue
            print(f"STATS: {count_bad_glyphs(text)}")
            print("TEXT-BEGIN")
            print(text)
            print("TEXT-END")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
