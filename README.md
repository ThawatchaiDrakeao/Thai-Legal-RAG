# Thai Legal RAG

ระบบ demo ถาม-ตอบกฎหมายไทย โดยมีการเชื่อมต่อ API ดังนี้:

```text
React/Vite frontend  →  FastAPI backend  →  Gemini API
   :5173                    :8000          Google AI Studio
```

## 1. ตั้งค่า Gemini API

สร้าง API key จาก Google AI Studio:

<https://aistudio.google.com/app/apikey>

จากนั้นสร้างไฟล์ `.env` ที่ root ของโปรเจกต์ โดยดูรูปแบบจาก [.env.example](.env.example):

```text
GOOGLE_API_KEY=ใส่คีย์จริงตรงนี้
```

ห้ามใส่ key ใน frontend และห้าม commit `.env` ขึ้น repository

## 2. เตรียมข้อมูลและรัน backend

จาก root `thai-legal-rag`:

```powershell
.\venv\Scripts\python.exe src\chunk_documents.py
.\venv\Scripts\python.exe src\build_embeddings.py
.\venv\Scripts\python.exe -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

ตรวจสถานะ backend:

```text
http://127.0.0.1:8000/health
```

API สำหรับถามคำถาม:

```text
POST http://127.0.0.1:8000/ask
Content-Type: application/json

{"question":"มาตรา 1 กล่าวถึงอะไร"}
```

## 3. รัน frontend

เปิด terminal อีกหน้าต่าง:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

เปิด <http://127.0.0.1:5173/> แล้ว frontend จะเรียก backend ที่ `http://127.0.0.1:8000` โดยอัตโนมัติ

ถ้าต้องการใช้ backend URL อื่น ให้คัดลอก `frontend/.env.example` เป็น `frontend/.env` แล้วแก้ค่า `VITE_API_URL`:

```text
VITE_API_URL=https://your-backend.example.com
```

## API response

`POST /ask` คืนคำตอบ พร้อม source และสถานะว่าพบบริบทหรือไม่:

```json
{
  "answer": "...",
  "sources": [
    {
      "text": "...",
      "source_file": "sample_law.txt",
      "page_number": null,
      "score": 0.8377
    }
  ],
  "found_context": true
}
```

## Tests

```powershell
.\venv\Scripts\python.exe -m pytest tests\ -v
```
