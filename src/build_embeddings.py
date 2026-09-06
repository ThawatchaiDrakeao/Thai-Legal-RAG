import json
import shutil
import sys
import tempfile
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
CHUNKS_PATH = PROCESSED_DIR / "chunks.json"
INDEX_PATH = PROCESSED_DIR / "faiss_index.bin"
META_PATH = PROCESSED_DIR / "meta.json"
MODEL_NAME = "intfloat/multilingual-e5-small"


def main():
    print("Loading chunks...")
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    if not chunks:
        raise ValueError(
            "No chunks found. Put .txt documents in data/raw and run "
            "chunk_documents.py first."
        )

    print("Loading embedding model:", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)

    # E5 models expect an explicit task prefix for good retrieval quality.
    texts = [f"passage: {c['text']}" for c in chunks]
    print("Encoding", len(texts), "chunks...")
    embeddings = model.encode(
        texts,
        batch_size=128,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    embeddings = np.asarray(embeddings, dtype="float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine similarity because vectors are normalized
    index.add(embeddings)

    # FAISS on Windows may not handle non-ASCII paths. Write to an ASCII
    # temporary path first, then move the completed file to the real path.
    with tempfile.NamedTemporaryFile(
        prefix="thai_legal_rag_", suffix=".bin", delete=False
    ) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        faiss.write_index(index, str(tmp_path))
        shutil.move(str(tmp_path), str(INDEX_PATH))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    print("Saved FAISS index to:", INDEX_PATH)

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print("Saved metadata to:", META_PATH)
    print("Done! Total vectors:", index.ntotal)


if __name__ == "__main__":
    main()
