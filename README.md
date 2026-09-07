# 🇹🇭 Thai Legal RAG

A production-oriented **Thai Legal Retrieval-Augmented Generation (RAG)** system for searching and answering questions about Thai law using official/legal text sources, semantic retrieval, exact article matching, and Google Gemini.

> ⚠️ **Demo / Portfolio Project** — This system is designed for demonstration and experimentation. It is **not legal advice** and should not be relied upon for real legal decisions.

---

## 🏗️ Architecture

```text
┌──────────────────────┐
│   React + Vite UI    │
│      Frontend        │
└──────────┬───────────┘
           │ HTTP
           ▼
┌──────────────────────┐
│      FastAPI         │
│       Backend        │
│                      │
│  /health             │
│  /ask                │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────┐
│       RAG Pipeline           │
│                              │
│  1. Article Number Detection │
│  2. Exact Article Matching   │
│  3. Semantic Retrieval       │
│  4. Context Construction     │
│  5. Gemini Generation        │
└──────────┬───────────────────┘
           │
      ┌────┴─────┐
      ▼          ▼
┌───────────┐ ┌────────────────┐
│ FAISS     │ │ Google Gemini  │
│ Vector DB │ │ gemini-2.5-flash│
└───────────┘ └────────────────┘
```

---

# ✨ Features

* 🇹🇭 Thai legal document retrieval
* 🔎 Exact article-number matching
* 🧠 Semantic vector search
* ⚡ FAISS cosine-similarity retrieval
* 🤖 Google Gemini `gemini-2.5-flash`
* 📚 Source/page citations
* 🚦 API rate limiting
* 🛡️ Context-grounded answering
* 🐳 Docker deployment
* ☁️ Render deployment
* 🧪 Automated regression tests
* 🔄 Reproducible document ingestion and embedding pipeline

---

# 🧰 Tech Stack

| Layer               | Technology                                                    |
| ------------------- | ------------------------------------------------------------- |
| Frontend            | React + Vite                                                  |
| Backend             | FastAPI                                                       |
| API Server          | Uvicorn                                                       |
| LLM                 | Google Gemini 2.5 Flash                                       |
| LLM SDK             | `google-genai`                                                |
| Embeddings          | FastEmbed + ONNX                                              |
| Embedding Model     | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Vector Search       | FAISS                                                         |
| Vector Dimension    | 384                                                           |
| Database            | FAISS index + JSON metadata                                   |
| Language Processing | PyThaiNLP                                                     |
| Container           | Docker                                                        |
| Deployment          | Render                                                        |
| Testing             | Pytest                                                        |
| CI                  | GitHub Actions                                                |

> The current production embedding implementation uses **FastEmbed/ONNX** instead of `sentence-transformers` + PyTorch to significantly reduce memory usage during deployment.

---

# 📚 Legal Corpus

The current production corpus contains **3,361 chunks**.

### 1. Civil and Commercial Code

Source:

```text
civil_commercial_code_snapshot.pdf
```

Approximately:

```text
2,906 chunks
```

The PDF is text-based and is used as the primary source for the Civil and Commercial Code.

---

### 2. Thai Penal Code

Source:

```text
penal_code_pythainlp.csv
```

Contains:

```text
452 records
Articles 1–398
```

The dataset is derived from the PyThaiNLP Thai-law corpus and is currently preferred over the OCR PDF because of encoding/OCR reliability.

---

### 3. Sample Law

```text
sample_law.txt
```

Contains:

```text
3 chunks
```

---

### ⚠️ OCR Source Excluded

```text
penal_code_snapshot.pdf
```

This source is intentionally excluded from production because the PDF uses problematic Private Use Area font encoding.

Attempts using:

* pypdf
* pdfplumber
* PyMuPDF
* Tesseract OCR
* image preprocessing
* multiple OCR resolutions

still produced unreliable article numbers and text.

Therefore, the structured PyThaiNLP CSV is used instead.

---

# 🔍 Retrieval Pipeline

The retrieval system uses a hybrid strategy.

## Step 1 — Detect Article Number

For queries such as:

```text
มาตรา 420 แห่งประมวลกฎหมายแพ่งและพาณิชย์กล่าวถึงเรื่องอะไร
```

the system detects:

```text
Article = 420
```

Thai numerals are also normalized.

Example:

```text
มาตรา ๔๒๐
```

→

```text
มาตรา 420
```

---

## Step 2 — Exact Article Matching

When an article number is detected, the system first searches metadata for the matching article.

This prevents semantic similarity from returning unrelated articles when the user explicitly asks about a particular provision.

Example:

```text
มาตรา 420
```

returns the corresponding:

```text
มาตรา 420
```

before semantic retrieval is considered.

---

## Step 3 — Semantic Search

For conceptual questions without an explicit article number, the system uses vector similarity search.

Embeddings are generated using:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

through:

```text
FastEmbed / ONNX
```

Vectors are normalized and searched using:

```text
FAISS IndexFlatIP
```

which is equivalent to cosine similarity when vectors are normalized.

---

# 🤖 RAG Generation

Retrieved legal context is passed to:

```text
Google Gemini
gemini-2.5-flash
```

The prompt instructs the model to:

* answer only from retrieved context
* avoid inventing legal information
* state when the available context is insufficient
* include source information

Example flow:

```text
User Question
      │
      ▼
Article Detection
      │
      ├── Article Found ──► Exact Match
      │
      └── No Article ─────► Semantic Search
                              │
                              ▼
                       Retrieved Context
                              │
                              ▼
                       Gemini 2.5 Flash
                              │
                              ▼
                           Answer
```

---

# 🚀 Getting Started

## 1. Clone Repository

```bash
git clone https://github.com/ThawatchaiDrakeao/Thai-Legal-RAG.git
cd Thai-Legal-RAG
```

---

# 🐍 Backend Setup

Recommended Python version:

```text
Python 3.11
```

Create virtual environment:

```bash
python -m venv venv
```

Activate on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Or Git Bash:

```bash
source venv/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create:

```text
.env
```

Add your Gemini API key:

```env
GOOGLE_API_KEY=your_google_ai_studio_api_key
```

The project uses Google AI Studio / Gemini API.

---

# 📦 Build Legal Corpus

The processed corpus can be reproduced from the raw sources.

Run:

```bash
python src/ingest_pdf.py
python src/ingest_csv.py
python src/chunk_documents.py
python src/build_embeddings.py
```

This generates:

```text
data/processed/
├── chunks.json
├── meta.json
└── index.faiss
```

The processed directory is intentionally excluded from Git because it can be regenerated.

---

# ▶️ Run Backend

```bash
python -m uvicorn src.api:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

# ❤️ Health Check

Example:

```json
{
  "status": "ok",
  "index_loaded": true,
  "vectors": 3361,
  "metadata_entries": 3361,
  "daily_requests_used": 0,
  "daily_requests_limit": 15,
  "minute_requests_used": 0,
  "minute_requests_limit": 4
}
```

---

# 🔌 API

## GET `/`

Returns basic service information.

Example:

```json
{
  "service": "Thai Legal RAG API",
  "status": "ok"
}
```

---

## GET `/health`

Returns service and vector-index status.

---

## POST `/ask`

Request:

```json
{
  "question": "มาตรา 420 แห่งประมวลกฎหมายแพ่งและพาณิชย์กล่าวถึงเรื่องอะไร"
}
```

Example response:

```json
{
  "answer": "...",
  "sources": [
    {
      "text": "...",
      "source_file": "civil_commercial_code_snapshot.pdf",
      "page_number": 75,
      "score": 1.0
    }
  ],
  "found_context": true
}
```

---

# 🧪 Testing

Run:

```bash
pytest tests/ -v
```

Current regression suite:

```text
6/6 tests passing
```

Important regression cases include:

* Article 289
* Article 373
* Article 1
* Article 420
* Full-sentence article queries
* Article IDs containing Thai prefixes such as `มาตรา 420`

---

# 🐳 Docker

The project includes a Docker deployment configuration.

Build:

```bash
docker build -t thai-legal-rag .
```

Run:

```bash
docker run --env-file .env -p 8000:8000 thai-legal-rag
```

The Docker image rebuilds the required legal chunks and vector index during the image build.

### Memory Optimization

The original implementation used:

```text
sentence-transformers
PyTorch
```

which caused excessive memory consumption on low-memory hosting.

The production implementation was changed to:

```text
FastEmbed
ONNX Runtime
paraphrase-multilingual-MiniLM-L12-v2
```

This reduced container memory usage substantially and resolved the Render free-tier OOM issue.

---

# ☁️ Deployment

Backend deployment:

```text
Render
```

Production service:

```text
https://thai-legal-rag.onrender.com
```

The backend is designed to run within the memory limitations of the Render free tier.

> Production deployment status should be verified through `/health` after each major deployment.

---

# 🚦 Rate Limiting

Because the project uses the Gemini free tier, the API implements a global application-level limiter.

Current application limits:

```text
4 requests / minute
15 requests / day
```

This provides a safety buffer below the reported Gemini project quota.

> These limits are intended for demo/portfolio usage, not high-volume production traffic.

---

# ⚠️ Limitations

This project currently has several limitations.

### Gemini Free Tier

The application relies on free-tier Gemini quota.

Therefore:

* requests are limited
* HTTP 429 can occur
* the system is not intended for high traffic

---

### Legal Accuracy

This system is a RAG demonstration.

It does not replace:

* lawyers
* legal professionals
* official legal databases
* current government publications

Legal information may also change over time.

---

### Corpus Coverage

The current corpus is intentionally limited.

It should not be considered a complete representation of Thai law.

---

### OCR

Some scanned legal PDFs contain problematic font encoding.

The project currently avoids unreliable OCR sources where structured text is available.

---

# 🛡️ Security / Reliability

Current safeguards include:

* API request validation
* maximum question length
* rate limiting
* context-grounded prompting
* separation of HTTP 429 from server errors
* deterministic retrieval
* regression testing
* reproducible vector-index generation

Future improvements:

* prompt-injection protection
* stronger input sanitization
* authentication
* distributed rate limiting
* monitoring / observability
* audit logging

---

# 🗂️ Project Structure

```text
thai-legal-rag/
│
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── data/
│   ├── raw/
│   └── processed/
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── src/
│   ├── api.py
│   ├── query.py
│   ├── rag_pipeline.py
│   ├── chunk_documents.py
│   ├── ingest_pdf.py
│   ├── ingest_csv.py
│   └── build_embeddings.py
│
├── tests/
│   └── ...
│
├── Dockerfile
├── requirements.txt
├── requirements-docker.txt
├── .gitignore
└── README.md
```

---

# 🔄 CI/CD

GitHub Actions automatically runs the project test pipeline.

The pipeline:

```text
Install dependencies
       ↓
Ingest PDF
       ↓
Ingest CSV
       ↓
Build chunks
       ↓
Build embeddings
       ↓
Run pytest
```

This ensures that the vector index can be reproducibly rebuilt from the source corpus.

---

# 📈 Current Project Status

| Component                      | Status     |
| ------------------------------ | ---------- |
| Legal corpus ingestion         | ✅          |
| PDF processing                 | ✅          |
| PyThaiNLP corpus               | ✅          |
| Chunking                       | ✅          |
| Metadata                       | ✅          |
| FAISS index                    | ✅          |
| Semantic retrieval             | ✅          |
| Exact article matching         | ✅          |
| Article 420 regression         | ✅          |
| Gemini integration             | ✅          |
| FastAPI                        | ✅          |
| Rate limiting                  | ✅          |
| Automated tests                | ✅ 6/6      |
| Docker                         | ✅          |
| OOM optimization               | ✅          |
| GitHub Actions                 | ✅          |
| Render deployment              | ✅ Deployed |
| Production health verification | ⏳          |
| React frontend                 | ✅ Local    |
| Frontend cloud deployment      | ⏳          |
| Prompt-injection guardrails    | ⏳          |
| Multi-turn memory              | ⏳          |
| Evaluation dataset             | ⏳          |
| PostgreSQL / pgvector          | ⏳          |

---

# 🧠 Engineering Highlights

This project demonstrates several practical AI Engineering concepts:

### RAG

```text
Documents
   ↓
Chunking
   ↓
Embeddings
   ↓
Vector Index
   ↓
Retrieval
   ↓
LLM
```

### Hybrid Retrieval

Rather than relying exclusively on semantic similarity:

```text
Exact Article Match
        +
Semantic Search
```

This is particularly important for legal questions where users frequently reference specific article numbers.

### Production Optimization

The project originally experienced memory limitations when deploying the embedding stack.

Replacing:

```text
PyTorch + Sentence Transformers
```

with:

```text
FastEmbed + ONNX Runtime
```

significantly reduced runtime memory consumption.

### Reproducibility

Processed vectors are not treated as the source of truth.

Instead:

```text
Raw Legal Data
      ↓
Ingestion
      ↓
Chunking
      ↓
Embedding
      ↓
FAISS
```

can be rebuilt through the CI/Docker pipeline.

---

# 🔮 Roadmap

## Phase 1 — Current

* [x] Legal corpus ingestion
* [x] Hybrid retrieval
* [x] Gemini integration
* [x] FastAPI
* [x] Docker
* [x] CI testing
* [x] Render deployment

## Phase 2

* [ ] Deploy React frontend
* [ ] Production `/health` verification
* [ ] Prompt-injection guardrails
* [ ] Better error handling
* [ ] Monitoring

## Phase 3

* [ ] Multi-turn conversation memory
* [ ] Evaluation dataset
* [ ] Retrieval quality metrics
* [ ] Precision / Recall / MRR evaluation
* [ ] Better citation handling

## Phase 4

* [ ] PostgreSQL
* [ ] pgvector
* [ ] Hybrid BM25 + vector search
* [ ] User authentication
* [ ] Production observability

---

# 👨‍💻 Author

**Thawatchai Drakeao**

Software Engineer · AI Engineering · Data Engineering

GitHub:

`https://github.com/ThawatchaiDrakeao/Thai-Legal-RAG`

---

# ⚖️ Disclaimer

This project is provided for educational and demonstration purposes only.

The generated answers may contain errors or incomplete information.

**Do not use this system as a substitute for professional legal advice or official legal sources.**
