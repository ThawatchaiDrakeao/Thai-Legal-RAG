"""Extract PDF pages with a targeted Thai OCR fallback."""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "pdf_pages.json"

OCR_FILENAME = "penal_code_snapshot.pdf"
PRIVATE_USE_THRESHOLD = 0.05
OCR_DPI = 400
OCR_PSM_CONFIG = "--psm 6"
LOW_CONFIDENCE_SUFFIX_RE = re.compile(r"(?<![0-9๐-๙])[0-9๐-๙]{3,4}(ทวิ|ตรี|จัตวา|เบญจ)")


def private_use_count(text):
    """Count BMP Private Use Area characters in a string."""
    return sum(0xE000 <= ord(char) <= 0xF8FF for char in text)


def needs_ocr(text, threshold=PRIVATE_USE_THRESHOLD):
    """Return True when the text layer is sufficiently corrupted."""
    if not text:
        return False
    return private_use_count(text) / len(text) > threshold


def preprocess_image(image):
    """Binarize and deskew a rendered page before sending it to Tesseract."""
    import cv2
    import numpy as np
    from PIL import Image

    grayscale = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(grayscale, (3, 3), 0)
    binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    coordinates = np.column_stack(np.where(binary < 255))
    if len(coordinates) < 10:
        return Image.fromarray(binary)

    angle = cv2.minAreaRect(coordinates)[-1]
    angle = -(90 + angle) if angle < -45 else -angle
    height, width = binary.shape
    center = (width // 2, height // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    deskewed = cv2.warpAffine(
        binary,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )
    return Image.fromarray(deskewed)


def low_confidence_suffixes(text):
    """Flag digit+suffix strings without whitespace for manual review."""
    return sorted(set(match.group(0) for match in LOW_CONFIDENCE_SUFFIX_RE.finditer(text)))


def ocr_page(document, page_index, dpi=OCR_DPI):
    """Render one PyMuPDF page and OCR it with Thai Tesseract."""
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "OCR dependencies are missing. Install pytesseract, PyMuPDF and Pillow."
        ) from exc

    tesseract_cmd = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract")
    if not tesseract_cmd:
        for candidate in (
            Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
            Path.home() / "tesseract-ocr" / "tesseract.exe",
        ):
            if candidate.exists():
                tesseract_cmd = str(candidate)
                break
    if not tesseract_cmd:
        raise RuntimeError(
            "Tesseract OCR engine not found. Install it and set TESSERACT_CMD "
            "or add tesseract.exe to PATH."
        )
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    page = document.load_page(page_index)
    scale = dpi / 72.0
    pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    image = preprocess_image(image)
    return pytesseract.image_to_string(image, lang="tha", config=OCR_PSM_CONFIG).strip()


def extract_pdf_pages(pdf_path, *, threshold=PRIVATE_USE_THRESHOLD, dpi=OCR_DPI,
                      page_number=None, page_numbers=None, force_ocr=False):
    """Extract one record per page, using 1-based page numbers."""
    pdf_path = Path(pdf_path)
    reader = PdfReader(str(pdf_path))
    if page_number is not None:
        target_pages = [page_number]
    elif page_numbers is not None:
        target_pages = page_numbers
    else:
        target_pages = range(1, len(reader.pages) + 1)
    use_ocr = pdf_path.name == OCR_FILENAME
    pages = []

    # PyMuPDF is native; give it an ASCII-only temporary filename.
    document = None
    temp_dir = None
    if use_ocr:
        import fitz

        temp_dir = tempfile.TemporaryDirectory(prefix="thai_legal_pdf_")
        ascii_pdf = Path(temp_dir.name) / "input.pdf"
        shutil.copy2(pdf_path, ascii_pdf)
        document = fitz.open(str(ascii_pdf))

    try:
        for current_page_number in target_pages:
            page = reader.pages[current_page_number - 1]
            text = (page.extract_text() or "").strip()
            extraction_method = "text"

            if use_ocr and (force_ocr or needs_ocr(text, threshold)):
                text = ocr_page(document, current_page_number - 1, dpi).strip()
                extraction_method = "ocr"

            if not text:
                continue
            pages.append(
                {
                    "id": f"{pdf_path.name}_page_{current_page_number}",
                    "source": pdf_path.name,
                    "source_file": pdf_path.name,
                    "page_number": current_page_number,
                    "extraction_method": extraction_method,
                    "ocr_low_confidence_patterns": (
                        low_confidence_suffixes(text) if extraction_method == "ocr" else []
                    ),
                    "text": text,
                }
            )
    finally:
        if document is not None:
            document.close()
        if temp_dir is not None:
            temp_dir.cleanup()

    return pages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--test-page",
        type=int,
        help="Extract and print one 1-based page without writing pdf_pages.json",
    )
    parser.add_argument(
        "--ocr-only",
        action="store_true",
        help="Re-OCR only pages already marked extraction_method=ocr in pdf_pages.json",
    )
    parser.add_argument("--ocr-dpi", type=int, default=OCR_DPI)
    parser.add_argument("--private-use-threshold", type=float, default=PRIVATE_USE_THRESHOLD)
    args = parser.parse_args()

    if args.test_page is not None:
        pdf_path = RAW_DIR / OCR_FILENAME
        pages = extract_pdf_pages(
            pdf_path,
            threshold=args.private_use_threshold,
            dpi=args.ocr_dpi,
            page_number=args.test_page,
            force_ocr=True,
        )
        if not pages:
            raise RuntimeError(f"No text extracted from page {args.test_page}")
        record = pages[0]
        bad = private_use_count(record["text"])
        print(f"Page: {record['page_number']}")
        print(f"Extraction method: {record['extraction_method']}")
        print(f"Private Use Area characters: {bad}")
        print(f"Low-confidence suffix patterns: {record['ocr_low_confidence_patterns']}")
        print("TEXT-BEGIN")
        print(record["text"])
        print("TEXT-END")
        return

    if args.ocr_only:
        if not OUTPUT_PATH.exists():
            raise RuntimeError("pdf_pages.json is missing; run the regular ingest first")
        with OUTPUT_PATH.open("r", encoding="utf-8") as file:
            existing_pages = json.load(file)
        target_pages = [
            page["page_number"]
            for page in existing_pages
            if page.get("source_file") == OCR_FILENAME
            and page.get("extraction_method") == "ocr"
        ]
        print(f"Re-OCR pages: {len(target_pages)}")
        updated_pages = extract_pdf_pages(
            RAW_DIR / OCR_FILENAME,
            threshold=args.private_use_threshold,
            dpi=args.ocr_dpi,
            page_numbers=target_pages,
            force_ocr=True,
        )
        updated_by_page = {page["page_number"]: page for page in updated_pages}
        for index, page in enumerate(existing_pages):
            if page.get("source_file") == OCR_FILENAME and page.get("page_number") in updated_by_page:
                existing_pages[index] = updated_by_page[page["page_number"]]
        with OUTPUT_PATH.open("w", encoding="utf-8") as file:
            json.dump(existing_pages, file, ensure_ascii=False, indent=2)
        print(f"Updated {len(updated_pages)} OCR pages in {OUTPUT_PATH}")
        return

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    all_pages = []
    pdf_files = sorted(RAW_DIR.glob("*.pdf"))

    for pdf_path in pdf_files:
        print("Processing:", pdf_path.name)
        pages = extract_pdf_pages(
            pdf_path,
            threshold=args.private_use_threshold,
            dpi=args.ocr_dpi,
        )
        all_pages.extend(pages)
        ocr_pages = sum(page["extraction_method"] == "ocr" for page in pages)
        print(f"  -> {len(pages)} pages with text ({ocr_pages} OCR pages)")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(all_pages, file, ensure_ascii=False, indent=2)

    print(f"Total saved: {len(all_pages)} PDF pages to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
