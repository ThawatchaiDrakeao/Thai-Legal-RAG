import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import ingest_pdf


def test_extract_pdf_pages_keeps_source_and_one_based_page_number(monkeypatch, tmp_path):
    class FakeReader:
        def __init__(self, path):
            assert path == str(tmp_path / "law.pdf")
            self.pages = [
                SimpleNamespace(extract_text=lambda: "มาตรา 1 ข้อความหน้าแรก"),
                SimpleNamespace(extract_text=lambda: "มาตรา 2 ข้อความหน้าสอง"),
            ]

    monkeypatch.setattr(ingest_pdf, "PdfReader", FakeReader)
    pdf_path = tmp_path / "law.pdf"
    pdf_path.write_bytes(b"mock pdf")

    pages = ingest_pdf.extract_pdf_pages(pdf_path)

    assert len(pages) == 2
    assert pages[0]["source_file"] == "law.pdf"
    assert pages[0]["page_number"] == 1
    assert pages[1]["page_number"] == 2
    assert pages[1]["text"] == "มาตรา 2 ข้อความหน้าสอง"
