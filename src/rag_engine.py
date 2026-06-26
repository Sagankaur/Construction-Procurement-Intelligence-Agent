import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .document_loader import SearchResult, search_query

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
MIN_RELEVANCE = 0.045
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "for",
    "from",
    "is",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "what",
    "which",
    "who",
    "with",
}


@dataclass
class SourceCard:
    """Structured source reference for a RAG response."""
    filename: str
    chunk_idx: int
    excerpt: str
    score: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RAGResponse:
    """Structured response from the RAG engine."""
    answer: str
    sources: List[SourceCard]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "sources": [s.to_dict() for s in self.sources],
        }


def _query_terms(query: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9\-]+", query.lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def build_prompt(query: str, chunks: list[SearchResult]) -> str:
    context = "\n\n".join(f"{chunk.label}: {chunk.chunk_text}" for chunk in chunks)
    return (
        "You are SiteSage AI, a construction procurement copilot. "
        "Answer only from the provided context. If the answer is not present, "
        "say you do not have enough information. Cite sources using the labels.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer with concise procurement actions and citations:"
    )


def _has_supported_context(query: str, chunks: list[SearchResult]) -> bool:
    if not chunks or chunks[0].score < MIN_RELEVANCE:
        return False
    terms = _query_terms(query)
    if not terms:
        return False
    context = " ".join(chunk.chunk_text.lower() for chunk in chunks)
    return bool(terms.intersection(set(re.findall(r"[a-zA-Z0-9\-]+", context))))


def _best_sentences(query: str, chunks: list[SearchResult], limit: int = 4) -> list[str]:
    terms = _query_terms(query)
    candidates: list[tuple[int, float, str]] = []
    for chunk in chunks:
        sentences = re.split(r"(?<=[.!?])\s+|;\s+", chunk.chunk_text)
        for sentence in sentences:
            clean = sentence.strip(" -")
            if len(clean) < 18:
                continue
            words = set(re.findall(r"[a-zA-Z0-9\-]+", clean.lower()))
            overlap = len(terms.intersection(words))
            if overlap:
                candidates.append((overlap, chunk.score, f"{clean} {chunk.label}"))
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    deduped: list[str] = []
    seen = set()
    for _, _, sentence in candidates:
        key = sentence.lower()
        if key in seen:
            continue
        deduped.append(sentence)
        seen.add(key)
        if len(deduped) == limit:
            break
    return deduped


def _fallback_answer(query: str, chunks: list[SearchResult]) -> str:
    sentences = _best_sentences(query, chunks)
    if not sentences:
        return (
            "I do not have enough information in the indexed procurement "
            "documents to answer that."
        )
    bullets = "\n".join(f"- {sentence}" for sentence in sentences)
    return f"Based on the indexed procurement documents:\n{bullets}"


def _ollama_enabled(use_ollama: Optional[bool]) -> bool:
    if use_ollama is not None:
        return use_ollama
    configured = os.getenv("SITESAGE_USE_OLLAMA", "1").lower() in {"1", "true", "yes"}
    return configured and shutil.which("ollama") is not None


def _call_ollama(prompt: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=35,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    answer = result.stdout.strip()
    return answer or None


def _build_source_cards(chunks: list[SearchResult]) -> List[SourceCard]:
    """Build source cards from search result chunks."""
    cards: List[SourceCard] = []
    for chunk in chunks:
        # Clean excerpt: first ~200 chars, trimmed to last complete word
        excerpt = chunk.chunk_text[:200].strip()
        if len(chunk.chunk_text) > 200:
            last_space = excerpt.rfind(" ")
            if last_space > 100:
                excerpt = excerpt[:last_space]
            excerpt += "…"
        cards.append(
            SourceCard(
                filename=chunk.filename,
                chunk_idx=chunk.chunk_idx,
                excerpt=excerpt,
                score=round(chunk.score, 4),
            )
        )
    # Sort by score descending
    cards.sort(key=lambda c: c.score, reverse=True)
    return cards


def get_answer(
    query: str,
    top_k: int = 4,
    db_path: Optional[Path] = None,
    use_ollama: Optional[bool] = None,
) -> RAGResponse:
    """Return a structured RAGResponse with answer text and source cards."""
    query = query.strip()
    if not query:
        return RAGResponse(
            answer="Ask a procurement question about indexed documents.",
            sources=[],
        )

    chunks = search_query(query, top_k=top_k, db_path=db_path)
    source_cards = _build_source_cards(chunks) if chunks else []

    if not _has_supported_context(query, chunks):
        return RAGResponse(
            answer=(
                "I do not have enough information in the indexed procurement "
                "documents to answer that."
            ),
            sources=source_cards,
        )

    prompt = build_prompt(query, chunks)
    if _ollama_enabled(use_ollama):
        answer = _call_ollama(prompt)
        if answer:
            return RAGResponse(answer=answer, sources=source_cards)

    return RAGResponse(
        answer=_fallback_answer(query, chunks),
        sources=source_cards,
    )
