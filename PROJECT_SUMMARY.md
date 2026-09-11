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
| Embedding | `alphaedge-ai/multilingual-e5-small-tha-16384` via `sentence-transformers` |
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

## Latest verified state (2026-09-11)

This section records the latest verified Docker and production-embedding work. Earlier sections remain historical project context.

### Current status

- The CPU-only production image was built and tested locally.
- The Render deployment was not pushed or deployed after this work, so production recovery is not yet verified.
- The previous Render incident remains the operational context: `/ask` failed while lazy-loading embedding resources. This change removes runtime Hugging Face dependency and CUDA/Torch ambiguity, but does not prove that the 512 MiB Render limit is sufficient.

### Root cause and Docker changes

- The verified runtime risks addressed here were an unpinned Torch dependency that could resolve to a non-CPU build and runtime model loading that could contact Hugging Face.
- `requirements-docker.txt` now installs `torch==2.13.0+cpu` from the official PyTorch CPU wheel index and explicitly pins `numpy==1.26.4`.
- The Docker build still uses `alphaedge-ai/multilingual-e5-small-tha-16384`, downloads it into `/app/.sentence_transformers_cache`, and sets `HF_HUB_OFFLINE=1` for runtime.
- Runtime model loading uses `local_files_only=True` in `src/query.py`; the index-building path in `src/build_embeddings.py` uses the same local-only behavior.
- SentenceTransformers version verified in the image: `6.0.1`.

### Image and runtime evidence

- `docker build --no-cache --progress=plain -t thai-legal-rag-diagnostic .` completed successfully.
- Image verification reported: `torch=2.13.0+cpu`, `cuda=False`, `sentence_transformers=6.0.1`, `numpy=1.26.4`, and `faiss=1.15.0`.
- The image contains the model weights (`model.safetensors`) and tokenizer/config/SentenceTransformer files. Cache size was approximately 108 MB.
- The build produced `data/processed/chunks.json`, `meta.json`, and `faiss_index.bin` with 3,361 records/vectors; the expected vector count is 3,361.
- No NVIDIA/CUDA packages were present in the image package inspection.
- Container RSS after model load reached `526.5 MiB` locally. Docker Desktop had 15.28 GiB available, so this is not Render evidence; it remains a blocker/risk against Render's 512 MiB limit.

### API and regression evidence

- Local container `/` and `/health` returned HTTP 200.
- One valid local `/ask` request for `มาตรา 420 มีความรับผิดอย่างไร` returned HTTP 200 with an answer, `found_context: true`, and sources from `civil_commercial_code_snapshot.pdf` (page 75, score 1.0). Article 420 behavior therefore remained verified for this request.
- Article 288 exact-match metadata verification found two matching records, from `civil_commercial_code_snapshot.pdf` and `pythainlp_thai_law`; no second `/ask` request was used for this check.
- Container logs confirmed baked-model loading without a runtime Hugging Face download/retry and showed the complete `[ASK]` sequence through a successful response.
- `python -m compileall src` passed.
- `pytest tests -q` passed: 6 tests.
- `git diff --check` passed with no whitespace errors.

### Files and commits

- The implementation commit changed only: `Dockerfile`, `requirements-docker.txt`, `src/build_embeddings.py`, and `src/query.py`.
- Previous diagnostic commit: `00e3c91 debug: add ask request diagnostics`.
- Current implementation commit: `5248818 fix: use CPU torch and offline baked embedding model`.
- `origin/main` remained at `00e3c91`; no push or Render deployment was performed.
- No secrets were included in the image or committed. `.env` was injected only for the local container test and remained excluded by `.dockerignore`.

### Remaining blockers

- Render must still be tested with the new commit. The local post-load RSS of 526.5 MiB exceeds the stated Render 512 MiB limit, so production success cannot be claimed.
- Experimental reranker work and its known limitations remain separate from this production image change.
