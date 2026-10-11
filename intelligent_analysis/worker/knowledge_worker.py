"""Knowledge index job handler: parse document, write chunks, activate index."""

from __future__ import annotations

import hashlib
from typing import Any

from ..knowledge.chunk import split_text
from ..knowledge.parse import read_document

PARSER_VERSION = "text-parser-0.4.0"
EMBEDDING_MODEL_VERSION = "keyword-tfidf-0.4.0"


def process_knowledge_job(
    store: Any,
    job_payload: dict[str, Any],
    lease: Any,
    now: Any,
) -> dict[str, Any]:
    """Process a knowledge_index job against C store.

    Expected job payload:
    - document_id: str
    - version: str
    - file_path: str (staged file on disk)
    - title, publisher, etc. (metadata may already be registered)

    Returns result_refs dict for jobs.complete_job.
    """
    document_id = job_payload["document_id"]
    version = job_payload["version"]
    file_path = job_payload["file_path"]

    with store.write() as uow:
        index_info = uow.knowledge.begin_index(
            document_id=document_id,
            version=version,
            job_id=lease.job_id,
            parser_version=PARSER_VERSION,
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lease=lease,
        )
        index_id = index_info["id"]

        text = read_document(file_path)
        chunks = split_text(text, document_id=document_id)

        chunk_inputs = [
            {
                "chunk_no": chunk.order,
                "text": chunk.text,
                "locator": f"chunk:{chunk.chunk_id}",
            }
            for chunk in chunks
        ]

        write_result = uow.knowledge.write_chunks(index_id, chunk_inputs, lease=lease)

        artifact_path = f"indices/{document_id}/{version}.json"
        artifact_content = hashlib.sha256(
            "".join(c.text for c in chunks).encode("utf-8")
        ).hexdigest()

        document = uow.knowledge.activate_index(
            document_id=document_id,
            version=version,
            artifact_path=artifact_path,
            artifact_sha256=artifact_content,
            expected_chunk_count=len(chunks),
            lease=lease,
        )

    return {
        "document_id": document_id,
        "version": version,
        "index_id": index_id,
        "chunk_count": len(chunks),
        "inserted": write_result["inserted"],
        "skipped": write_result["skipped"],
        "document_index_status": document.get("index_status", "ready"),
    }
