# Thai Legal RAG — Project Context

เอกสารนี้มีไว้ให้ AI coding assistant เช่น GPT หรือ Claude อ่านก่อนช่วยวางแผนและพัฒนาโปรเจกต์ต่อ

## 1. เป้าหมายโปรเจกต์

สร้างระบบถาม-ตอบกฎหมายไทยแบบ RAG (Retrieval-Augmented Generation) โดยใช้เอกสารกฎหมายจริงเป็นแหล่งอ้างอิง ระบบต้องค้นหาข้อความที่เกี่ยวข้องจากเอกสารก่อน แล้วส่งเฉพาะบริบทนั้นให้ Gemini สร้างคำตอบ

ข้อกำหนดสำคัญ:

- คำตอบต้องอ้างอิงจากบริบทที่ค้นพบเท่านั้น
- หากเอกสารไม่มีข้อมูลเพียงพอ ต้องแจ้งว่าไม่พบข้อมูลที่เกี่ยวข้อง
- ควรแสดงแหล่งที่มาของข้อมูลและคะแนน retrieval ให้ผู้ใช้ตรวจสอบได้
- ระบบนี้เป็นต้นแบบเพื่อการศึกษา ไม่ใช่คำปรึกษากฎหมายจากทนายความ

## 2. เทคโนโลยี

- Python และ virtual environment ที่โฟลเดอร์ `venv/`
- LLM: Google Gemini `gemini-2.5-flash`
- SDK: `google-genai`
- Embedding model: `intfloat/multilingual-e5-small` (เลือกเพื่อให้ rebuild corpus ขนาดใหญ่ได้เหมาะกับ CPU demo)
- Vector search: FAISS โดยใช้ inner product กับ normalized embeddings ซึ่งเทียบเท่า cosine similarity
- Input ปัจจุบัน: ไฟล์ `.txt` ใน `data/raw/`
- Dependency หลักอยู่ใน `requirements.txt`

## 3. โครงสร้างโปรเจกต์

```text
thai-legal-rag/
├─ data/
│  ├─ raw/                  # เอกสารกฎหมายต้นฉบับ เช่น sample_law.txt
│  └─ processed/            # chunks และ vector index ที่สร้างแล้ว
├─ src/
│  ├─ chunk_documents.py    # แบ่งเอกสารตามคำว่า มาตรา
│  ├─ build_embeddings.py   # สร้าง embeddings และ FAISS index
│  ├─ query.py              # โหลด index และค้นหาเอกสารที่เกี่ยวข้อง
│  ├─ rag_pipeline.py       # retrieval + Gemini answer
│  └─ test_gemini.py        # ทดสอบการเชื่อมต่อ Gemini
├─ .env                     # secret/API key; ห้าม commit หรือคัดลอกค่าออกมา
├─ requirements.txt
├─ PROJECT_SUMMARY.md
└─ context.md               # เอกสารสำหรับ AI assistant
```

## 4. Data flow

```text
data/raw/*.txt + *.pdf
    ↓
ingest_pdf.py (สำหรับ PDF)
    ↓
chunk_documents.py
    ↓
data/processed/chunks.json
    ↓
build_embeddings.py
    ↓
data/processed/faiss_index.bin + meta.json
    ↓
query.py: embedding คำถาม → FAISS top-k
    ↓
rag_pipeline.py: ส่งบริบท + คำถามให้ Gemini
```

## 5. สถานะปัจจุบัน

ทำเสร็จแล้ว:

- ตั้งค่า Python virtual environment แล้ว
- ติดตั้ง/ตรวจสอบ `faiss` และ `sentence-transformers` ใน venv แล้ว
- แบ่ง `data/raw/sample_law.txt` ได้ 3 chunks สำเร็จ
- ปรับ path ให้ยึดจาก root ของโปรเจกต์ ไม่ขึ้นกับ current working directory
- ปรับ embedding ให้ใช้ `passage:` สำหรับเอกสาร และ `query:` สำหรับคำถาม ตามรูปแบบของ E5
- เปลี่ยน RAG pipeline จาก OpenAI ให้ใช้ Gemini SDK ตาม tech stack ของโปรเจกต์
- รองรับทั้ง `GOOGLE_API_KEY` และ `GEMINI_API_KEY` โดยไม่เปิดเผยค่า key
- ตรวจ Python syntax ของไฟล์ใน `src/` ผ่านแล้ว
- เพิ่ม PDF snapshot จริงใน `data/raw/`: อาญา 143 หน้า และแพ่งพาณิชย์ 306 หน้า
- ingest แล้ว 449 หน้า ได้ 3,903 PDF chunks และรวม sample เป็น 3,906 chunks
- สร้าง FAISS index และ metadata สำเร็จ โดยมี 3,906 vectors
- query ทดสอบพบทั้ง `penal_code_snapshot.pdf` และ `civil_commercial_code_snapshot.pdf`
- มี tests 5 เคสใน `tests/` และรันผ่านทั้งหมด
- มี FastAPI API ใน `src/api.py` และ React/Vite demo ใน `frontend/`

ยังค้างอยู่:

- เอกสารที่มีเป็น snapshot; ต้องตรวจราชกิจจานุเบกษา/กฤษฎีกาอีกครั้งก่อนใช้งานจริง
- ยังไม่มี automated test สำหรับ API endpoint โดยตรง
- ยังไม่มี OCR สำหรับ PDF แบบ scanned/image
- ยังไม่มี deployment configuration
- `PROJECT_SUMMARY.md` อาจมีข้อความ encoding เพี้ยนเมื่ออ่านผ่าน Windows console บางแบบ ควรตรวจและบันทึกเป็น UTF-8 หากแก้ไข

## 6. คำสั่งรัน

รันจาก root `thai-legal-rag` บน PowerShell:

```powershell
.\venv\Scripts\python.exe src\chunk_documents.py
.\venv\Scripts\python.exe src\build_embeddings.py
.\venv\Scripts\python.exe src\rag_pipeline.py
```

ทดสอบ Gemini แยกต่างหาก:

```powershell
.\venv\Scripts\python.exe src\test_gemini.py
```

ถ้าโมเดลดาวน์โหลดไม่สำเร็จ ให้ตรวจ network/Hugging Face ก่อน ไม่ควรเปลี่ยน embedding model โดยไม่พิจารณาความเข้ากันได้กับข้อมูลภาษาไทย

## 7. จุดที่ควรทำต่อ ตามลำดับ

1. สร้าง FAISS index ให้สำเร็จ และตรวจว่ามีไฟล์ `faiss_index.bin` กับ `meta.json`
2. ทดสอบ retrieval ด้วยคำถามภาษาไทย เช่น `มาตรา 1 กล่าวถึงอะไร` และตรวจ source/score
3. ทดสอบ RAG end-to-end ด้วยคำถามที่มีคำตอบอยู่และคำถามนอกขอบเขต
4. เพิ่ม validation เช่น index กับ metadata ต้องมีจำนวนรายการตรงกัน และ `top_k` ต้องไม่เกินจำนวน vectors
5. เพิ่ม automated tests สำหรับ chunking, retrieval และ prompt construction
6. เพิ่มการอ่าน PDF โดยเก็บชื่อไฟล์/เลขหน้าเป็น metadata
7. เพิ่ม citation ที่ละเอียดขึ้น เช่น ชื่อเอกสารและเลขมาตรา
8. ค่อยพิจารณาทำ FastAPI หรือ UI หลัง pipeline หลักเสถียร

## 8. ข้อควรระวังสำหรับ AI assistant

- อ่านไฟล์จริงก่อนแก้ อย่าสมมติว่า `PROJECT_SUMMARY.md` สะท้อนสถานะล่าสุดทั้งหมด
- ห้ามแสดงหรือ commit ค่า API key จาก `.env`
- อย่าใช้กฎหมายจากความจำแทนเอกสารที่ค้นพบในระบบ
- การเปลี่ยน model, chunking strategy หรือ prompt ควรทดสอบกับข้อมูลภาษาไทย
- ก่อนสรุปว่างานเสร็จ ให้รัน syntax check และทดสอบคำสั่งจริงอย่างน้อยหนึ่งรอบ
- โฟลเดอร์นี้อาจไม่มี Git repository ที่ใช้งานได้ จึงควรตรวจ `git status` ก่อนอ้างอิง diff หรือ commit

## 9. รูปแบบคำตอบที่ต้องการจาก AI assistant

เมื่อเริ่มงาน ให้รายงานสั้น ๆ ว่า:

1. ตรวจพบสถานะปัจจุบันอะไร
2. งานที่กำลังจะทำและเหตุผล
3. ไฟล์ใดจะถูกแก้
4. วิธีทดสอบผลลัพธ์
5. ปัญหาหรือสิ่งที่ต้องให้เจ้าของโปรเจกต์ตัดสินใจ (ถ้ามี)
