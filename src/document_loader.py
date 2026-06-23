import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import HashingVectorizer

from .database import get_connection, get_project_root, save_procurement_facts

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
        from pypdf import PdfReader
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


def extract_procurement_facts(text: str) -> list[dict]:
    """Extract structured procurement facts from document text using regex."""
    facts: list[dict] = []

    # PO / Purchase Order numbers
    for match in re.finditer(r"\b(PO[-\s]?\d{3,6})\b", text, re.IGNORECASE):
        facts.append({"field": "PO Number", "value": match.group(1).upper(), "confidence": "high"})

    # Dates (YYYY-MM-DD, DD/MM/YYYY, Month DD YYYY, etc.)
    date_patterns = [
        r"\b(\d{4}[-/]\d{2}[-/]\d{2})\b",
        r"\b(\d{2}[-/]\d{2}[-/]\d{4})\b",
        r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
    ]
    for pat in date_patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            facts.append({"field": "Date", "value": match.group(1), "confidence": "high"})

    # Monetary values
    for match in re.finditer(
        r"(?:INR|Rs\.?|USD|\$|₹)\s*([\d,]+(?:\.\d{1,2})?)"
        r"|([\d,]+(?:\.\d{1,2})?)\s*(?:INR|Rs|USD|lakhs?|crores?)",
        text, re.IGNORECASE,
    ):
        value = match.group(1) or match.group(2)
        if value:
            facts.append({"field": "Contract Value", "value": value.strip(), "confidence": "medium"})

    # Quantities with units
    for match in re.finditer(
        r"(\d+(?:\.\d+)?)\s*(ton(?:ne)?s?|kg|m[²³]?|cubic[_ ]?met(?:er|re)s?"
        r"|km|units?|pieces?|bags?|liters?|gallons?|sqft|sq\.?\s*ft)",
        text, re.IGNORECASE,
    ):
        facts.append({
            "field": "Quantity",
            "value": f"{match.group(1)} {match.group(2)}",
            "confidence": "medium",
        })

    # Construction material keywords
    material_keywords = [
        "structural steel", "rebar", "tmt", "concrete", "cement", "copper cable",
        "formwork", "aggregate", "bricks", "tiles", "glass", "plywood",
        "reinforcement", "bitumen", "pipes", "sanitary", "electrical",
        "hvac", "generator", "elevator", "waterproofing",
    ]
    text_lower = text.lower()
    seen_materials: set[str] = set()
    for keyword in material_keywords:
        if keyword in text_lower and keyword not in seen_materials:
            seen_materials.add(keyword)
            facts.append({"field": "Material", "value": keyword.title(), "confidence": "medium"})

    # Vendor / company names (pattern: capitalized multi-word names near keywords)
    vendor_patterns = [
        r"(?:vendor|supplier|contractor|from|by)[:\s]+([A-Z][A-Za-z&]+(?:\s+[A-Z][A-Za-z&]+){0,3})",
    ]
    for pat in vendor_patterns:
        for match in re.finditer(pat, text):
            name = match.group(1).strip()
            if len(name) > 3:
                facts.append({"field": "Vendor", "value": name, "confidence": "medium"})

    # Deduplicate
    seen: set[tuple[str, str]] = set()
    unique_facts: list[dict] = []
    for fact in facts:
        key = (fact["field"], fact["value"])
        if key not in seen:
            seen.add(key)
            unique_facts.append(fact)

    return unique_facts


def store_document(file_name: str, raw_bytes: bytes, db_path: Optional[Path] = None) -> tuple[int, list[dict]]:
    """Store a document and return (doc_id, extracted_facts)."""
    text = extract_text(file_name, raw_bytes)
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("No extractable text found in document.")

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

    # Extract and save procurement facts
    facts = extract_procurement_facts(text)
    if facts:
        save_procurement_facts(doc_id, facts, db_path)

    return doc_id, facts


def _load_chunks(db_path: Optional[Path] = None) -> list[SearchResult]:
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
            doc_id, _ = store_document(path.name, path.read_bytes(), db_path)
            seeded.append(doc_id)
    return seeded