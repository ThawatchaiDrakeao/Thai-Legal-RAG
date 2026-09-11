# Thai Legal RAG

Thai Legal RAG is a Thai legal-domain Retrieval-Augmented Generation (RAG) application. It retrieves relevant legal context from a structured corpus, then uses Google Gemini to generate an answer with the retrieved sources. The system combines FastAPI, SentenceTransformers, FAISS, and Gemini. It is an educational and portfolio project, not legal advice.

## Demo / Production

Production URL: <https://thai-legal-rag.onrender.com>

Production smoke verification has been performed successfully. Long-term stability, soak testing, Render memory behavior, and production Hugging Face runtime-download behavior have not been independently verified.

Verified endpoints:

- `GET /` — service status
- `GET /health` — health and request-quota status
- `POST /ask` — answer generation with retrieved sources

## Problem

Thai legal information is difficult to query naturally across multiple source documents and legal domains. This project explores a retrieval-first approach: retrieve relevant legal passages before asking an LLM to formulate an answer.

## Architecture

```text
User
  -> FastAPI /ask
  -> article-number detection and exact-match retrieval
     or semantic retrieval
  -> SentenceTransformers query embedding
  -> FAISS similarity search
  -> retrieved legal context
  -> Gemini generation
  -> answer + sources
```

Retrieval and generation are separate stages. FAISS and the retrieval code select context; Gemini generates the response from that context.

## RAG Pipeline

1. Ingest legal source files.
2. Chunk the documents and preserve source metadata.
3. Generate normalized embeddings.
4. Build a FAISS `IndexFlatIP` index.
5. Detect explicit article numbers and perform exact metadata matching when present.
6. Use semantic retrieval to fill the result set.
7. Pass the selected context to Gemini.
8. Return the answer together with source text, source file, page, and score fields.

The verified corpus contains 3,361 vectors in a 384-dimensional FAISS index. The corpus includes the Civil and Commercial Code snapshot, the PyThaiNLP Thai-law dataset, and a small sample law source. The structured PyThaiNLP dataset is preferred over the problematic penal-code OCR PDF.

### Legal sources

- `civil_commercial_code_snapshot.pdf` — primary Civil and Commercial Code source.
- `penal_code_pythainlp.csv` — structured Thai-law records covering Articles 1–398.
- `sample_law.txt` — small sample source used by the ingestion pipeline.
- `penal_code_snapshot.pdf` is excluded from the production corpus because its font encoding produced unreliable OCR/article text.

## Embedding Model

The current Docker/production embedding configuration uses:

```text
alphaedge-ai/multilingual-e5-small-tha-16384
```

The model is loaded through SentenceTransformers `6.0.1` and used for Thai/multilingual query and document embeddings. The verified Docker image bakes the model into `/app/.sentence_transformers_cache` and uses local/offline loading at runtime.

No benchmark superiority claim is made here; the documented metrics are the verified index dimensions and vector count.

## LLM

The RAG pipeline uses Google Gemini through the `google-genai` SDK. The source code calls:

```text
gemini-2.5-flash
```

The prompt instructs Gemini to answer from the retrieved legal context and identify the available source information.

## Docker / Deployment Engineering

The Docker dependency stack was made deterministic for CPU inference. The verified configuration:

- `torch==2.13.0+cpu`
- official PyTorch CPU wheel index
- `numpy==1.26.4`
- `sentence-transformers==6.0.1`
- model downloaded during image build
- `HF_HUB_OFFLINE=1` at runtime
- `local_files_only=True` for model loading
- no NVIDIA/CUDA packages in the verified image

The container does not require GPU inference, so CPU-only PyTorch avoids unnecessary CUDA dependencies and makes the image/runtime dependency choice more deterministic. The local image reached 526.5 MiB peak RSS after model load; this is local Docker evidence only and is not a Render memory measurement.

## API

### `GET /`

Returns basic service information.

```json
{
  "service": "Thai Legal RAG API",
  "status": "ok"
}
```

### `GET /health`

Returns service status and the in-process daily/minute request counters. It is intentionally lightweight and does not force lazy resource loading.

### `POST /ask`

Request schema:

```json
{
  "question": "มาตรา 420 มีความรับผิดอย่างไร"
}
```

The `question` field is required, must contain 1–2,000 characters, and the response contains `answer`, `sources`, and `found_context`:

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

The application uses global limits of 4 requests per minute and 15 requests per day for the demo service.

## Verification

| Verification | Result |
|---|---|
| Docker build | PASS |
| CPU-only PyTorch | `2.13.0+cpu` |
| `torch.cuda.is_available()` | `False` |
| SentenceTransformers | `6.0.1` |
| FAISS vectors | 3,361 |
| FAISS dimension | 384 |
| `python -m compileall src` | PASS |
| `pytest` | 6 passed |
| Production `GET /` | HTTP 200 |
| Production `GET /health` | HTTP 200, status `ok` |
| Production `POST /ask` | HTTP 200 in smoke verification |
| Production Article 420 | PASS |
| Production Article 288 | PASS with known civil/criminal collision |

Production smoke verification is successful for the checks above. It is not a claim of 24/7 reliability, long-term stability, or production-scale performance.

## Example Regression Checks

### Article 420

Question:

```text
มาตรา 420 มีความรับผิดอย่างไร
```

Verified in production:

- HTTP 200
- answer returned
- `found_context: true`
- Civil and Commercial Code source retrieved
- page 75 returned with score 1.0

### Article 288

Question:

```text
มาตรา 288 มีโทษอย่างไร
```

Verified in production:

- HTTP 200
- answer returned
- `found_context: true`
- criminal Article 288 source retrieved from `pythainlp_thai_law`

The same article number also occurs in the civil corpus, so a civil Article 288 result can appear in the retrieved sources. This known collision has not been fixed by the current implementation.

## Project Structure

```text
thai-legal-rag/
├── .github/workflows/tests.yml
├── data/
│   ├── raw/
│   └── processed/
├── frontend/
├── scripts/
├── src/
│   ├── api.py
│   ├── build_embeddings.py
│   ├── chunk_documents.py
│   ├── ingest_csv.py
│   ├── ingest_pdf.py
│   ├── query.py
│   └── rag_pipeline.py
├── tests/
├── Dockerfile
├── requirements.txt
├── requirements-docker.txt
├── PROJECT_SUMMARY.md
└── README.md
```

## Known Limitations

1. Article 288 has a civil/criminal article-number collision that can create retrieval ambiguity.
2. The Render memory limit has not been independently verified.
3. Render production OOM behavior has not been independently verified.
4. Render Hugging Face runtime-download behavior could not be verified because production logs were unavailable.
5. Long-term production stability and soak testing have not been performed.
6. The corpus is limited and should not be treated as a complete representation of Thai law.
7. Some scanned legal PDFs have unreliable font encoding; the affected penal-code OCR source is excluded in favor of structured text.
8. Gemini free-tier quota can produce HTTP 429 responses.

## Development / Local Run

Create a virtual environment and install the Python dependencies:

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set `GOOGLE_API_KEY` or `GEMINI_API_KEY` in `.env` for Gemini requests. The application also accepts the existing `.env.example` as a starting point.

To run the API locally:

```bash
python -m uvicorn src.api:app --reload
```

The local API is available at `http://127.0.0.1:8000`, with interactive documentation at `/docs`.

To build the Docker image used for the verified CPU/offline model path:

```bash
docker build -t thai-legal-rag .
docker run --env-file .env -p 8000:8000 thai-legal-rag
```

## Testing

Run the verified checks:

```bash
python -m compileall src
pytest
```

The verified test result is 6 passed tests.

## Engineering Highlights

- Thai-language legal RAG with source-aware responses
- Hybrid exact article matching and semantic retrieval
- FAISS vector search with SentenceTransformers embeddings
- FastAPI API design with validation and quota protection
- CPU-only PyTorch dependency selection for Docker
- Model baking and offline runtime loading
- Reproducible ingestion and FAISS index generation
- Production smoke verification and regression checks
- Evidence-based debugging of deployment/runtime behavior

## Continuous Integration

The repository includes `.github/workflows/tests.yml` for the project test pipeline. The local verification recorded for this version is 6 passed tests; no additional benchmark or accuracy metric is claimed here.

## Repository

GitHub: <https://github.com/ThawatchaiDrakeao/Thai-Legal-RAG>

## Status

Production smoke verified.

The core API works for the verified production smoke checks, including Article 420 and Article 288 retrieval. Long-term stability and Render memory behavior remain unverified, and the Article 288 civil/criminal collision remains a known limitation.

## License / Disclaimer

This project is provided for educational and demonstration purposes only. Generated answers may be incomplete or incorrect. Do not use this system as a substitute for professional legal advice or official legal sources.
