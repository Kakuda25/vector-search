from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

from app.utils.env_loader import get_db_config
from app.utils.vector_utils import adjust_dimension, parse_vector_string

MODEL_NAME = "intfloat/multilingual-e5-large"

app = FastAPI(title="PostgreSQL Vector Search UI API", version="0.1.0")

web_dir = Path(__file__).resolve().parent.parent / "web"
app.mount("/assets", StaticFiles(directory=str(web_dir)), name="assets")

_model_cache: SentenceTransformer | None = None
_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


class SimilaritySearchRequest(BaseModel):
    type: str = Field(pattern="^(product|text)$")
    productId: int | None = None
    text: str | None = None
    topK: int = Field(default=10, ge=1, le=50)
    scoreThreshold: float = Field(default=0.0, ge=-1.0, le=1.0)
    category: str | None = None


class EmbeddingJobRequest(BaseModel):
    mode: str = Field(pattern="^(all|missing)$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_connection():
    cfg = get_db_config()
    if not cfg["password"]:
        raise HTTPException(status_code=500, detail="POSTGRES_PASSWORD が未設定です")
    return psycopg2.connect(
        host=cfg["host"],
        port=cfg["port"],
        database=cfg["database"],
        user=cfg["user"],
        password=cfg["password"],
    )


def _get_model() -> SentenceTransformer:
    global _model_cache
    if _model_cache is None:
        _model_cache = SentenceTransformer(MODEL_NAME)
    return _model_cache


def _normalize_query_text(text: str) -> str:
    if text.startswith("query: "):
        return text
    return f"query: {text}"


def _normalize_passage_text(text: str) -> str:
    if text.startswith("passage: "):
        return text
    return f"passage: {text}"


def _search_with_vector(query_embedding: np.ndarray, top_k: int, score_threshold: float, category: str | None):
    conn = _get_connection()
    try:
        cur = conn.cursor()
        # 現行スキーマには category カラムがないため、category フィルタは将来拡張とする。
        cur.execute(
            """
            SELECT id, product_code, name, description, price, embedding
            FROM products
            WHERE embedding IS NOT NULL
            ORDER BY id
            """
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    vectors = []
    products = []
    for pid, code, name, description, price, embedding_str in rows:
        vec = parse_vector_string(embedding_str)
        vec = adjust_dimension(vec, len(query_embedding))
        vectors.append(vec)
        products.append((pid, code, name, description, float(price)))

    matrix = np.array(vectors, dtype=np.float32)
    similarity = np.dot(matrix, query_embedding.astype(np.float32))
    ranking = np.argsort(similarity)[::-1]

    results = []
    for idx in ranking:
        score = float(similarity[idx])
        if score < score_threshold:
            continue
        pid, code, name, description, price = products[idx]
        results.append(
            {
                "productId": pid,
                "productCode": code,
                "name": name,
                "description": description or "",
                "price": price,
                "category": None,
                "score": round(score, 6),
                "rank": len(results) + 1,
            }
        )
        if len(results) >= top_k:
            break
    return results


def _run_embedding_job(job_id: str, mode: str):
    with _jobs_lock:
        _jobs[job_id]["status"] = "running"
        _jobs[job_id]["startedAt"] = _now_iso()

    conn = _get_connection()
    model = _get_model()
    try:
        cur = conn.cursor()
        where_clause = "WHERE embedding IS NULL" if mode == "missing" else ""
        cur.execute(
            f"""
            SELECT id, product_code, name, description
            FROM products
            {where_clause}
            ORDER BY id
            """
        )
        targets = cur.fetchall()

        with _jobs_lock:
            _jobs[job_id]["total"] = len(targets)

        success_count = 0
        failures = []

        for product_id, product_code, name, description in targets:
            text = _normalize_passage_text(f"{name} {description or ''}".strip())
            try:
                embedding = model.encode(text, normalize_embeddings=True, convert_to_numpy=True)
                embedding = adjust_dimension(embedding)
                embedding_str = "[" + ",".join(map(str, embedding.tolist())) + "]"
                cur.execute(
                    """
                    UPDATE products
                    SET embedding = %s::vector(1536)
                    WHERE id = %s
                    """,
                    (embedding_str, product_id),
                )
                success_count += 1
            except Exception as exc:  # noqa: BLE001
                failures.append({"productId": product_id, "productCode": product_code, "reason": str(exc)})

            with _jobs_lock:
                _jobs[job_id]["successCount"] = success_count
                _jobs[job_id]["failCount"] = len(failures)
                _jobs[job_id]["progress"] = (success_count + len(failures)) / max(len(targets), 1)
                _jobs[job_id]["failures"] = failures

        conn.commit()
        with _jobs_lock:
            _jobs[job_id]["status"] = "done"
            _jobs[job_id]["finishedAt"] = _now_iso()
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        with _jobs_lock:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = str(exc)
            _jobs[job_id]["finishedAt"] = _now_iso()
    finally:
        conn.close()


@app.get("/")
def root():
    return FileResponse(str(web_dir / "index.html"))


@app.get("/api/system/health")
def system_health():
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        has_vector = cur.fetchone() is not None
        conn.close()
        return {"api": "ok", "db": "ok", "pgvector": "ok" if has_vector else "ng", "checkedAt": _now_iso()}
    except Exception:  # noqa: BLE001
        return {"api": "ok", "db": "ng", "pgvector": "ng", "checkedAt": _now_iso()}


@app.get("/api/dashboard/summary")
def dashboard_summary():
    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) AS total,
                   COUNT(embedding) AS embedded
            FROM products
            """
        )
        total, embedded = cur.fetchone()
    finally:
        conn.close()
    return {"totalProducts": total, "embeddedProducts": embedded, "missingEmbeddings": total - embedded}


@app.get("/api/products")
def get_products(q: str | None = None, embeddingStatus: str | None = None, limit: int = 100):
    conn = _get_connection()
    try:
        cur = conn.cursor()
        conditions = []
        params: list[Any] = []

        if q:
            conditions.append("(name ILIKE %s OR product_code ILIKE %s)")
            params.extend([f"%{q}%", f"%{q}%"])
        if embeddingStatus == "embedded":
            conditions.append("embedding IS NOT NULL")
        elif embeddingStatus == "missing":
            conditions.append("embedding IS NULL")

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)
        cur.execute(
            f"""
            SELECT id, product_code, name, price, (embedding IS NOT NULL) AS embedded
            FROM products
            {where_sql}
            ORDER BY id
            LIMIT %s
            """,
            tuple(params),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    return {
        "items": [
            {
                "id": row[0],
                "productCode": row[1],
                "name": row[2],
                "category": None,
                "price": float(row[3]),
                "embeddingStatus": "embedded" if row[4] else "missing",
            }
            for row in rows
        ]
    }


@app.post("/api/similarity/search")
def similarity_search(payload: SimilaritySearchRequest):
    model = _get_model()
    if payload.type == "product":
        if payload.productId is None:
            raise HTTPException(status_code=400, detail="productId が必要です")
        conn = _get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT embedding FROM products WHERE id = %s AND embedding IS NOT NULL", (payload.productId,))
            row = cur.fetchone()
        finally:
            conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="対象商品の embedding が見つかりません")
        query_embedding = parse_vector_string(row[0])
    else:
        if not payload.text:
            raise HTTPException(status_code=400, detail="text が必要です")
        q = _normalize_query_text(payload.text)
        query_embedding = model.encode(q, normalize_embeddings=True, convert_to_numpy=True)
        query_embedding = adjust_dimension(query_embedding)

    items = _search_with_vector(query_embedding, payload.topK, payload.scoreThreshold, payload.category)
    return {"query": payload.model_dump(), "items": items}


@app.post("/api/embeddings/jobs")
def create_embedding_job(payload: EmbeddingJobRequest):
    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {
            "jobId": job_id,
            "mode": payload.mode,
            "status": "queued",
            "progress": 0.0,
            "total": 0,
            "successCount": 0,
            "failCount": 0,
            "failures": [],
            "error": None,
            "createdAt": _now_iso(),
            "startedAt": None,
            "finishedAt": None,
        }

    thread = threading.Thread(target=_run_embedding_job, args=(job_id, payload.mode), daemon=True)
    thread.start()
    return {"jobId": job_id, "status": "queued"}


@app.get("/api/embeddings/jobs/{job_id}")
def get_embedding_job(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job が見つかりません")
    return job


@app.get("/api/embeddings/failures")
def get_embedding_failures(jobId: str):
    with _jobs_lock:
        job = _jobs.get(jobId)
    if not job:
        raise HTTPException(status_code=404, detail="job が見つかりません")
    return {"items": job.get("failures", [])}
