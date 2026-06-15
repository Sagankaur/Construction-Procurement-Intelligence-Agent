import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import HashingVectorizer

from .database import get_connection, get_project_root, init_db

CHUNK_SIZE = 700
CHUNK_OVERLAP = 120
VECTOR_DIM = 512

_VECTORIZER = HashingVectorizer(
    n_features=VECTOR_DIM,
    alternate_sign=False,
    norm="l2",
    lowercase=True,
    token_pattern=r"(?u)\b[\w\-]+\b",
)


@dataclass(frozen=True)
class SearchResult:
    doc_id: int
    filename: str
    chunk_idx: int
    chunk_text: str
    score: float

    @property
    def label(self) -> str:
        return f"[{self.filename}#c{self.chunk_idx}]"


def extract_text(file_name: str, raw_bytes: bytes) -> str:
    ext = Path(file_name).suffix.lower()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if ext in {".txt", ".md", ".csv"}:
        return raw_bytes.decode("utf-8", errors="ignore")
    if ext in {".xlsx", ".xls"}:
        df = pd.read_excel(io.BytesIO(raw_bytes))
        return df.to_csv(index=False)
    raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(start + CHUNK_SIZE, len(clean))
        chunks.append(clean[start:end].strip())
        if end == len(clean):
            break
        start = max(0, end - CHUNK_OVERLAP)
    return chunks


def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.empty((0, VECTOR_DIM), dtype="float32")
    matrix = _VECTORIZER.transform(texts)
    return matrix.astype(np.float32).toarray()


def store_document(file_name: str, raw_bytes: bytes, db_path: Optional[Path] = None) -> int:
    text = extract_text(file_name, raw_bytes)
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("No extractable text found in document.")

    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO documents (filename, content) VALUES (?, ?)",
        (Path(file_name).name, text),
    )
    doc_id = int(cur.lastrowid)
    cur.executemany(
        "INSERT INTO document_chunks (doc_id, chunk_idx, chunk_text) VALUES (?, ?, ?)",
        [(doc_id, idx, chunk) for idx, chunk in enumerate(chunks)],
    )
    conn.commit()
    conn.close()
    return doc_id


def _load_chunks(db_path: Optional[Path] = None) -> list[SearchResult]:
    init_db(db_path)
    conn = get_connection(db_path)
    rows = conn.execute(
        """
        SELECT
            c.doc_id,
            d.filename,
            c.chunk_idx,
            c.chunk_text
        FROM document_chunks c
        JOIN documents d ON d.id = c.doc_id
        ORDER BY c.id
        """
    ).fetchall()
    conn.close()
    return [
        SearchResult(
            doc_id=int(row["doc_id"]),
            filename=str(row["filename"]),
            chunk_idx=int(row["chunk_idx"]),
            chunk_text=str(row["chunk_text"]),
            score=0.0,
        )
        for row in rows
    ]


def search_query(
    query: str,
    top_k: int = 4,
    db_path: Optional[Path] = None,
) -> list[SearchResult]:
    query = query.strip()
    if not query:
        return []

    rows = _load_chunks(db_path)
    if not rows:
        return []

    embeddings = embed_texts([row.chunk_text for row in rows])
    query_vec = embed_texts([query])
    index = faiss.IndexFlatIP(VECTOR_DIM)
    index.add(embeddings)
    distances, indices = index.search(query_vec, min(top_k, len(rows)))

    results: list[SearchResult] = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        row = rows[int(idx)]
        results.append(
            SearchResult(
                doc_id=row.doc_id,
                filename=row.filename,
                chunk_idx=row.chunk_idx,
                chunk_text=row.chunk_text,
                score=float(dist),
            )
        )
    return results


def document_exists(filename: str, db_path: Optional[Path] = None) -> bool:
    init_db(db_path)
    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT 1 FROM documents WHERE filename = ? LIMIT 1",
        (Path(filename).name,),
    ).fetchone()
    conn.close()
    return row is not None


def seed_sample_documents(db_path: Optional[Path] = None) -> list[int]:
    docs_dir = get_project_root() / "docs"
    seeded: list[int] = []
    for sample in ["sample_purchase_order.txt", "sample_vendor_contract.txt"]:
        path = docs_dir / sample
        if path.exists() and not document_exists(path.name, db_path):
            seeded.append(store_document(path.name, path.read_bytes(), db_path))
    return seeded
