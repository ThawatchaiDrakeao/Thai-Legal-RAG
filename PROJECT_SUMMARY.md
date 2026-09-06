# Thai Legal RAG - สรุปโปรเจกต์

## เป้าหมาย

สร้างระบบ RAG (Retrieval-Augmented Generation) สำหรับตอบคำถามด้านกฎหมายไทย โดยใช้เอกสารกฎหมายจริงเป็นฐานความรู้ แล้วให้ AI ตอบโดยอ้างอิงจากบริบทที่ค้นพบเท่านั้น

ระบบนี้เป็นต้นแบบเพื่อการศึกษา ไม่ใช่คำปรึกษากฎหมายจากทนายความ

## Tech Stack

| ส่วนประกอบ | เครื่องมือที่ใช้ |
|---|---|
| ภาษา | Python |
| LLM | Google Gemini (`gemini-2.5-flash`, free tier) |
| SDK | `google-genai` |
| Embedding | `intfloat/multilingual-e5-small` |
| Vector search | FAISS + normalized inner product (cosine similarity) |
| Retrieval | Hybrid: exact article-number match + semantic search |
| Backend API | FastAPI + Uvicorn พร้อม global rate limiting |
| Frontend | React + Vite (`frontend/`) |
| Environment | Python venv ที่ `venv/` |
| OS / Terminal | Windows + PowerShell/Git Bash |

## Corpus ปัจจุบัน (production index)

| แหล่งข้อมูล | รูปแบบ | สถานะ |
|---|---|---|
| `sample_law.txt` | ข้อความตัวอย่าง | ใช้งานจริง (3 chunks) |
| ประมวลกฎหมายแพ่งและพาณิชย์ | PDF (text-based, สะอาด) | ใช้งานจริง (~2,900 chunks) |
| ประมวลกฎหมายอาญา | CSV จาก [PyThaiNLP/thai-law](https://github.com/PyThaiNLP/thai-law) (hand-labeled, public domain) | ใช้งานจริง (452 มาตรา, มาตรา 1-398 ครบ) |
| ประมวลกฎหมายอาญา (PDF + OCR) | PDF scan + Tesseract OCR | **ไม่ใช้ใน production** — ดู "ข้อจำกัดที่ทราบ" ด้านล่าง |

รวม FAISS index ปัจจุบัน: **3,361 vectors**

## ข้อจำกัดที่ทราบ (Known Limitations)

### 1. PDF อาญา (penal_code_snapshot.pdf) ถูกตัดออกจาก production pipeline

**สาเหตุ**: หน้า PDF ต้นฉบับมีปัญหา font encoding (Private Use Area characters แทนสระ/วรรณยุกต์) ลองแก้หลายทาง:
- เปลี่ยนไลบรารี extract (pypdf, pdfplumber, PyMuPDF) → ได้ผลเหมือนกันหมด ไม่ช่วย
- OCR ด้วย Tesseract (250 DPI) → อ่านสระ/วรรณยุกต์ถูกแล้ว แต่เลขมาตราคลาดเคลื่อนหนัก (297/435 suspicious findings)
- ปรับปรุง OCR (400 DPI + binarization + deskew + psm 6) → แทบไม่ต่างจากเดิม (298/435) ยืนยันว่าไม่ใช่ปัญหา config

**ทางแก้ที่ใช้จริง**: เปลี่ยนไปใช้ PyThaiNLP/thai-law CSV dataset แทน (hand-labeled, public domain, มาจาก krisdika.go.th) sanity check ผ่าน 100% (0 out-of-order, 0 duplicate, 0 gap)

**เก็บไว้เป็นทางเลือกสำรอง**: โค้ด PDF/OCR (`src/ingest_pdf.py`) และไฟล์ PDF เดิมยังอยู่ครบ เผื่อในอนาคตหา PDF ต้นฉบับที่ encoding ถูกต้องได้ ดู `scripts/validate_ocr_quality.py`, `scripts/sample_ocr_findings.py` สำหรับกระบวนการตรวจสอบที่ใช้

### 2. Gemini API free tier — quota ต่ำมาก

**ยืนยันจาก production**: `gemini-2.5-flash` free tier จำกัดที่ **5 requests/นาที และ 20 requests/วัน** (quota ระดับ project ไม่ใช่ per-user)

**การป้องกัน**: `src/api.py` มี global rate limiter (4/นาที, 15/วัน — ต่ำกว่า quota จริงของ Gemini เพื่อเผื่อ buffer) และแยก HTTP 429 (quota exceeded) ออกจาก 500 (server error จริง) ชัดเจน

**ผลกระทบ**: เหมาะสำหรับ demo เฉพาะกิจ/สัมภาษณ์งาน ไม่เหมาะสำหรับใช้งานจริงที่มีผู้ใช้พร้อมกันหลายคน — ถ้าจะ deploy ใช้งานจริงต้องอัปเกรดเป็น paid tier

## ความคืบหน้า

- [x] Pipeline หลัก: chunking → embedding → FAISS → Gemini ทำงานสมบูรณ์
- [x] Hybrid retrieval: ถามเลขมาตราตรงๆ ได้ exact match เสมอ (แก้ปัญหา semantic search พลาดมาตราที่ใกล้เคียงกันทางตัวเลข)
- [x] Automated tests: `tests/` ผ่านครบ 5/5 (`pytest tests/ -v`)
- [x] FastAPI backend (`/health`, `/ask`) พร้อม global rate limiting และ error handling ที่แยก 429/500
- [x] React/Vite frontend พร้อม source citation, loading state, disclaimer
- [x] Corpus 3 แหล่งครบ (sample + แพ่งพาณิชย์ + อาญา ผ่าน PyThaiNLP CSV)
- [ ] ทดสอบ `/ask` end-to-end ผ่าน API จริงอีกรอบ (รอ Gemini quota reset)
- [ ] Docker
- [ ] Cloud deployment
- [ ] Guardrails เพิ่มเติม (prompt injection defense)
- [ ] Multi-turn conversation memory

## โครงสร้างไฟล์ปัจจุบัน

```text
data/raw/sample_law.txt                        เอกสารกฎหมายตัวอย่าง
data/raw/civil_commercial_code_snapshot.pdf     ประมวลกฎหมายแพ่งและพาณิชย์ (ใช้งานจริง)
data/raw/penal_code_snapshot.pdf                ประมวลกฎหมายอาญา PDF (สำรอง ไม่ใช้ใน production)
data/raw/penal_code_pythainlp.csv               ประมวลกฎหมายอาญา จาก PyThaiNLP (ใช้งานจริง)
data/raw/SOURCES.md                             แหล่งที่มาและข้อจำกัดของข้อมูลทุกแหล่ง
data/processed/chunks.json                      chunks ปัจจุบัน (3,361 รายการ)
data/processed/faiss_index.bin, meta.json       production index
data/processed/pythainlp_articles.json          ข้อมูล CSV ที่ normalize แล้ว
data/processed/pdf_pages.json                   ข้อความ PDF รายหน้า (รวมของที่ไม่ได้ใช้)
src/ingest_pdf.py                               อ่าน PDF + OCR fallback (สำรอง)
src/ingest_csv.py                               อ่าน PyThaiNLP CSV (ใช้งานจริง)
src/chunk_documents.py                          รวม chunks จากทุกแหล่ง (กรอง penal_code_snapshot.pdf ออก)
src/build_embeddings.py                         สร้าง embeddings และ FAISS index
src/query.py                                    hybrid retrieval (exact match + semantic)
src/rag_pipeline.py                             retrieval + Gemini answer + citation
src/api.py                                      FastAPI backend พร้อม rate limiting
scripts/validate_ocr_quality.py                 ตรวจสอบคุณภาพ OCR (diagnostic, ไม่ใช้ใน production)
scripts/sample_ocr_findings.py                  สุ่มตรวจผล OCR ด้วยตา
scripts/compare_pdf_extract.py                  เทียบ pypdf/pdfplumber/PyMuPDF
scripts/validate_pythainlp_csv.py               ตรวจสอบคุณภาพ CSV ก่อน rebuild
frontend/                                       React/Vite web demo
tests/                                          automated tests (5 passed)
context.md                                      บริบทสำหรับ AI assistant
README.md                                       คู่มือติดตั้งและรัน
