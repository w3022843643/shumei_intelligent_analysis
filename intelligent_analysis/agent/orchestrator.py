"""Minimal RAG assistant orchestrator."""

from __future__ import annotations

from uuid import UUID, uuid4

from ..contracts import ChatResponse
from ..knowledge.index import InMemoryKnowledgeIndex
from ..knowledge.retrieve import retrieve
from .citations import document_citation


def answer_with_index(
    message: str,
    index: InMemoryKnowledgeIndex,
    conversation_id: UUID | None = None,
) -> ChatResponse:
    matches = retrieve(index, message)
    if not matches:
        return ChatResponse(
            conversation_id=conversation_id or uuid4(),
            answer="抱歉，当前知识库中没有检索到足以回答该问题的资料。",
            status="insufficient_evidence",
            limitations=["No matching authorized document was found."],
        )

    citations = [document_citation(document, chunk) for document, chunk, _ in matches]
    evidence = "\n".join(f"- {chunk.text}" for _, chunk, _ in matches)
    answer = f"根据已授权资料，可参考以下信息：\n{evidence}"
    return ChatResponse(
        conversation_id=conversation_id or uuid4(),
        answer=answer,
        status="answered",
        citations=citations,
        limitations=["This answer is based only on retrieved authorized documents."],
    )
