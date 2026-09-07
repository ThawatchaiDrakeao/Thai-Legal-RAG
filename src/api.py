import re
import sys
import threading
import time
from collections import deque
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from .query import has_relevant_context, load
    from .rag_pipeline import answer_question
except ImportError:  # Supports: uvicorn api:app --app-dir src
    from query import has_relevant_context, load
    from rag_pipeline import answer_question

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ---- Gemini free-tier limits for gemini-2.5-flash (as observed):
# 5 requests/minute, 20 requests/day. These are GLOBAL per-project quotas,
# shared across all users of this demo -- not per-IP. We stay comfortably
# below both to avoid ever hitting Gemini's own 429.
GLOBAL_RPM_LIMIT = 4
GLOBAL_DAILY_LIMIT = 15

_daily_lock = threading.Lock()
_daily_state = {"date": date.today(), "count": 0}

_minute_lock = threading.Lock()
_minute_window = deque()  # timestamps of recent requests, for a 60s sliding window


def _check_and_increment_daily_cap():
    with _daily_lock:
        today = date.today()
        if _daily_state["date"] != today:
            _daily_state["date"] = today
            _daily_state["count"] = 0
        if _daily_state["count"] >= GLOBAL_DAILY_LIMIT:
            return False
        _daily_state["count"] += 1
        return True


def _check_and_record_minute_window():
    now = time.monotonic()
    with _minute_lock:
        while _minute_window and now - _minute_window[0] > 60:
            _minute_window.popleft()
        if len(_minute_window) >= GLOBAL_RPM_LIMIT:
            return False
        _minute_window.append(now)
        return True


def get_usage_snapshot():
    with _daily_lock:
        daily_used = _daily_state["count"]
    with _minute_lock:
        now = time.monotonic()
        minute_used = sum(1 for t in _minute_window if now - t <= 60)
    return {
        "daily_requests_used": daily_used,
        "daily_requests_limit": GLOBAL_DAILY_LIMIT,
        "minute_requests_used": minute_used,
        "minute_requests_limit": GLOBAL_RPM_LIMIT,
    }


_QUOTA_ERROR_PATTERN = re.compile(r"RESOURCE_EXHAUSTED|429", re.IGNORECASE)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class Source(BaseModel):
    text: str
    source_file: str
    page_number: Optional[int] = None
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    found_context: bool


app = FastAPI(
    title="Thai Legal RAG API",
    description="Retrieval-Augmented Generation API for Thai legal documents",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_resources():
    return load()


@app.get("/")
def root():
    return {"service": "Thai Legal RAG API", "status": "ok"}


@app.get("/health")
def health():
    try:
        index, meta, _ = get_resources()
        return {
            "status": "ok",
            "index_loaded": True,
            "vectors": index.ntotal,
            "metadata_entries": len(meta),
            **get_usage_snapshot(),
        }
    except Exception as exc:
        return {
            "status": "degraded",
            "index_loaded": False,
            "vectors": 0,
            "error": str(exc),
        }


@app.post("/ask", response_model=AskResponse)
def ask(request: Request, body: AskRequest):
    if not _check_and_increment_daily_cap():
        raise HTTPException(
            status_code=429,
            detail=(
                f"ระบบถึงขีดจำกัดการใช้งานประจำวันแล้ว ({GLOBAL_DAILY_LIMIT} ครั้ง/วัน "
                "เนื่องจากใช้ Gemini API free tier) กรุณาลองใหม่พรุ่งนี้"
            ),
        )
    if not _check_and_record_minute_window():
        raise HTTPException(
            status_code=429,
            detail=(
                f"มีคนใช้งานพร้อมกันเยอะเกินไปในขณะนี้ (จำกัด {GLOBAL_RPM_LIMIT} "
                "คำถาม/นาทีทั้งระบบ เนื่องจากใช้ Gemini API free tier) "
                "กรุณารอสักครู่แล้วลองใหม่"
            ),
        )
    try:
        index, meta, model = get_resources()
        answer, contexts = answer_question(
            body.question, index, meta, model, top_k=3
        )
        sources = [
            Source(
                text=item["text"],
                source_file=item["source_file"],
                page_number=item.get("page_number"),
                score=item["score"],
            )
            for item in contexts
        ]
        return AskResponse(
            answer=answer,
            sources=sources,
            found_context=has_relevant_context(contexts),
        )
    except Exception as exc:
        if _QUOTA_ERROR_PATTERN.search(str(exc)):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API free tier หมด quota ชั่วคราว กรุณาลองใหม่ในอีกสักครู่ "
                    "(ระบบนี้ใช้ free tier ซึ่งมีข้อจำกัดการใช้งานต่ำ)"
                ),
            ) from exc
        raise HTTPException(
            status_code=500,
            detail=f"ไม่สามารถประมวลผลคำถามได้: {exc}",
        ) from exc
