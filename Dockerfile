FROM python:3.11-slim

# Tesseract OCR (ยังเก็บไว้เผื่อใช้ src/ingest_pdf.py ในอนาคต แม้ production ปัจจุบันไม่ได้ใช้)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-tha \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Bake embedding model เข้า image ตอน build เพื่อไม่ต้องดาวน์โหลดใหม่ทุกครั้งที่ container เริ่ม
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-small')"

COPY src/ ./src/
COPY data/processed/chunks.json data/processed/faiss_index.bin data/processed/meta.json ./data/processed/

EXPOSE 8000

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
