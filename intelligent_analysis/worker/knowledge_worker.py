"""Prepare a portable knowledge artifact for publication by D after C commit."""
import hashlib
import json

from ..contracts import DocumentMetadata
from ..knowledge.chunk import split_text
from ..knowledge.index import InMemoryKnowledgeIndex
from ..knowledge.parse import read_document


def process_knowledge_job(job_payload: dict) -> dict:
    document_id = job_payload["document_id"]
    metadata = DocumentMetadata.model_validate(job_payload["metadata"])
    chunks = split_text(read_document(job_payload["file_path"]), document_id=document_id)
    if not chunks:
        raise ValueError("Document has no extractable text")
    payload = {"documents": {document_id: {
        "metadata": metadata.model_dump(mode="json"),
        "chunks": [c.model_dump(mode="json") for c in chunks]}}}
    artifact = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return {"document_id": document_id, "version": job_payload["version"],
            "chunk_count": len(chunks), "artifact_bytes": artifact,
            "artifact_sha256": hashlib.sha256(artifact).hexdigest(),
            "chunks": [{"chunk_no": c.order, "text": c.text,
                        "locator": {"chunk_id": c.chunk_id, "order": c.order}}
                       for c in chunks], "snapshot": payload}


def publish_knowledge_snapshot(snapshot: dict, path: str) -> None:
    """D calls with the full committed active snapshot, under its publish lock.

    Replacing a full snapshot prevents stale retry artifacts overwriting newer
    document versions. E does not publish uncommitted computation by itself.
    """
    from ..contracts import TextChunk
    index = InMemoryKnowledgeIndex()
    for document_id, document in snapshot["documents"].items():
        chunks = [TextChunk.model_validate(c) for c in document["chunks"]]
        if any(c.document_id != document_id for c in chunks):
            raise ValueError("Chunk identity mismatch")
        index.add_document(document_id, DocumentMetadata.model_validate(document["metadata"]), chunks)
    index.save(path)
