import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import rag_pipeline


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def generate_content(self, *, model, contents, config):
        # Mock Gemini: no network call or API key is needed for pytest.
        if "ภาษีมูลค่าเพิ่ม" in contents:
            return FakeResponse("ไม่พบข้อมูลที่เกี่ยวข้องในเอกสารที่ให้มา")
        return FakeResponse("มาตรา 1 กล่าวถึงชื่อประมวลกฎหมายแพ่งและพาณิชย์ อ้างอิง source: sample_law.txt")


class FakeGeminiClient:
    models = FakeModels()


@pytest.fixture(scope="module", autouse=True)
def mock_gemini_client():
    original_client = rag_pipeline.client
    rag_pipeline.client = FakeGeminiClient()
    yield
    rag_pipeline.client = original_client


def test_in_scope_question_returns_answer_and_source_reference():
    answer = rag_pipeline.generate_answer("มาตรา 1 กล่าวถึงอะไร")

    assert answer.strip()
    assert "source" in answer.lower()
    assert "sample_law.txt" in answer


def test_out_of_scope_question_reports_missing_information():
    answer = rag_pipeline.generate_answer("กฎหมายภาษีมูลค่าเพิ่มคืออะไร")

    assert any(phrase in answer for phrase in ("ไม่พบข้อมูล", "ไม่มีข้อมูล", "ไม่พบ"))
