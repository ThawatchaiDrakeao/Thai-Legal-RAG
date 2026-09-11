FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-tha \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

RUN python -c "import torch; torch.set_num_threads(1); from sentence_transformers import SentenceTransformer; SentenceTransformer('alphaedge-ai/multilingual-e5-small-tha-16384', cache_folder='/app/.sentence_transformers_cache')"

ENV HF_HUB_OFFLINE=1

COPY src/ ./src/
COPY data/raw/sample_law.txt data/raw/civil_commercial_code_snapshot.pdf data/raw/penal_code_pythainlp.csv ./data/raw/

RUN mkdir -p data/processed && \
    python src/ingest_pdf.py && \
    python src/ingest_csv.py && \
    python src/chunk_documents.py && \
    python src/build_embeddings.py

EXPOSE 8000

CMD ["sh", "-c", "uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-8000}"]  
