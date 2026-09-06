import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai

try:
    from .query import load, search
except ImportError:  # Supports running with: python src/rag_pipeline.py
    from query import load, search

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None


def format_citation(item):
    if item.get("source") == "pythainlp_thai_law":
        article = item.get("article_number") or item.get("article_id") or "ไม่ทราบ"
        return (
            f"มาตรา {article} (ที่มา: PyThaiNLP Thai Law Dataset, "
            f"{item.get('license', 'public domain')}, อ้างอิงจากกฤษฎีกา)"
        )
    location = item.get("source_file", item.get("source", "ไม่ทราบแหล่งที่มา"))
    if item.get("page_number") is not None:
        location += f", หน้า {item['page_number']}"
    return location


def build_prompt(question, contexts):
    context_text = "\n\n".join(
        f"[citation={format_citation(item)}, source_url={item.get('source_url')}]\n{item['text']}"
        for item in contexts
    )
    return f"""คุณคือผู้ช่วยด้านกฎหมายไทย ตอบคำถามโดยอ้างอิงจากบริบทด้านล่างเท่านั้น
ถ้าไม่มีข้อมูลเพียงพอ ให้บอกว่าไม่พบข้อมูลที่เกี่ยวข้อง
กรุณาระบุชื่อ source ที่ใช้อ้างอิงในคำตอบด้วย

บริบท:
{context_text}

คำถาม: {question}

คำตอบ:"""


def answer_question(question, index, meta, model, top_k=3):
    if client is None:
        raise RuntimeError(
            "ไม่พบ API key สำหรับ Gemini ให้ตั้ง GOOGLE_API_KEY หรือ GEMINI_API_KEY ใน .env"
        )

    contexts = search(question, index, meta, model, top_k=top_k)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=build_prompt(question, contexts),
        config={"temperature": 0.2},
    )
    return response.text, contexts


def generate_answer(query_text: str, top_k: int = 3):
    index, meta, model = load()
    answer, _ = answer_question(query_text, index, meta, model, top_k=top_k)
    return answer


if __name__ == "__main__":
    print("ระบบ RAG พร้อมใช้งาน (พิมพ์ 'exit' เพื่อออก)")
    index, meta, model = load()
    while True:
        question = input("\nคำถาม: ")
        if question.strip().lower() == "exit":
            break
        answer, contexts = answer_question(question, index, meta, model)
        print("\nคำตอบ:\n" + answer)
        print("\nแหล่งอ้างอิง:")
        for item in contexts:
            page = f", page={item['page_number']}" if item["page_number"] is not None else ""
            url = f" url={item['source_url']}" if item.get("source_url") else ""
            print(f"- {format_citation(item)}{page} (score={item['score']:.3f}){url}")
