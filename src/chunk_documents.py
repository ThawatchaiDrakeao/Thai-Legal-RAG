import os
import re
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
PDF_PAGES_PATH = PROCESSED_DIR / "pdf_pages.json"
PYTHAINLP_ARTICLES_PATH = PROCESSED_DIR / "pythainlp_articles.json"

EXCLUDED_PDF_SOURCES = {"penal_code_snapshot.pdf"}


def _thai_to_arabic_digits(text):
    thai_digits = "๐๑๒๓๔๕๖๗๘๙"
    arabic_digits = "0123456789"
    return text.translate(str.maketrans(thai_digits, arabic_digits))


def _extract_article_number(text):
    match = re.search(r"มาตรา\s*([๐-๙0-9]+)", text)
    if not match:
        return None

    normalized = _thai_to_arabic_digits(match.group(1))
    return int(normalized)


def chunk_by_mattra(text):
    pattern = r"(มาตรา\s*[๐-๙0-9]+)"
    parts = re.split(pattern, text)

    chunks = []
    current_chunk = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if re.fullmatch(r"มาตรา\s*[๐-๙0-9]+", part):
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = part + " "
        else:
            current_chunk += part

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_by_mattra(text)

    result = []
    for i, chunk in enumerate(chunks):
        article_number = _extract_article_number(chunk)

        result.append(
            {
                "id": os.path.basename(filepath) + "_" + str(i),
                "source": os.path.basename(filepath),
                "source_file": os.path.basename(filepath),
                "page_number": None,
                "article_id": (
                    f"มาตรา {article_number}"
                    if article_number is not None
                    else None
                ),
                "article_number": article_number,
                "text": chunk,
            }
        )

    return result


def process_pdf_pages(exclude_sources=EXCLUDED_PDF_SOURCES):
    if not PDF_PAGES_PATH.exists():
        return []

    with open(PDF_PAGES_PATH, "r", encoding="utf-8") as f:
        pages = json.load(f)

    skipped = 0
    result = []

    for page in pages:
        if page.get("source_file") in exclude_sources:
            skipped += 1
            continue

        chunks = chunk_by_mattra(page.get("text", ""))

        for i, chunk in enumerate(chunks):
            article_number = _extract_article_number(chunk)

            result.append(
                {
                    "id": f"{page['source_file']}_page_{page['page_number']}_{i}",
                    "source": page["source_file"],
                    "source_file": page["source_file"],
                    "page_number": page["page_number"],
                    "article_id": (
                        f"มาตรา {article_number}"
                        if article_number is not None
                        else None
                    ),
                    "article_number": article_number,
                    "text": chunk,
                }
            )

    if skipped:
        print(
            f"Skipped {skipped} pages from excluded PDF sources: "
            f"{exclude_sources}"
        )

    return result


def process_pythainlp_articles():
    """Load normalized CSV records without re-splitting their article text."""
    if not PYTHAINLP_ARTICLES_PATH.exists():
        return []

    with open(PYTHAINLP_ARTICLES_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)

    result = []
    for article in articles:
        result.append(
            {
                "id": article["id"],
                "source": article["source"],
                "source_file": article.get("source_file", article["source"]),
                "page_number": None,
                "article_id": article.get("article_id"),
                "article_number": article.get("article_number"),
                "phak": article.get("phak"),
                "laksana": article.get("laksana"),
                "muad": article.get("muad"),
                "suan": article.get("suan"),
                "source_url": article.get("source_url"),
                "license": article.get("license"),
                "notes": article.get("notes", ""),
                "text": article["text"],
            }
        )

    return result


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    all_chunks = []

    for filename in os.listdir(RAW_DIR):
        if filename.endswith(".txt"):
            filepath = RAW_DIR / filename
            print("Processing:", filename)

            chunks = process_file(filepath)
            all_chunks.extend(chunks)

            print("  ->", len(chunks), "chunks")

    pdf_chunks = process_pdf_pages()

    if pdf_chunks:
        print("Adding PDF chunks:", len(pdf_chunks))
        all_chunks.extend(pdf_chunks)

    csv_chunks = process_pythainlp_articles()

    if csv_chunks:
        print("Adding PyThaiNLP CSV chunks:", len(csv_chunks))
        all_chunks.extend(csv_chunks)

    output_path = PROCESSED_DIR / "chunks.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print("Total saved:", len(all_chunks), "chunks to", output_path)


if __name__ == "__main__":
    main()
