"""Minimal in-memory keyword knowledge index."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..contracts import DocumentMetadata, TextChunk


def tokenize(text: str) -> set[str]:
    lowered = text.lower()
    latin_terms = {token for token in re.split(r"[^\w]+|_", lowered) if token and not _is_cjk(token)}
    cjk_chars = {char for char in lowered if _is_cjk(char)}
    return latin_terms | cjk_chars


def _is_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


@dataclass
class IndexedDocument:
    metadata: DocumentMetadata
    chunks: list[TextChunk]


@dataclass
class InMemoryKnowledgeIndex:
    documents: dict[str, IndexedDocument] = field(default_factory=dict)

    def add_document(self, document_id: str, metadata: DocumentMetadata, chunks: list[TextChunk]):
        self.documents[document_id] = IndexedDocument(metadata=metadata, chunks=chunks)

    def search(self, query: str, top_k: int = 3) -> list[tuple[float, IndexedDocument, TextChunk]]:
        query_terms = tokenize(query)
        matches: list[tuple[float, IndexedDocument, TextChunk]] = []
        for document in self.documents.values():
            for chunk in document.chunks:
                chunk_terms = tokenize(chunk.text)
                overlap = len(query_terms & chunk_terms)
                if overlap:
                    score = overlap / max(len(query_terms), 1)
                    matches.append((score, document, chunk))
        return sorted(matches, key=lambda item: (-item[0], item[2].order))[:top_k]

    def __len__(self) -> int:
        return len(self.documents)
