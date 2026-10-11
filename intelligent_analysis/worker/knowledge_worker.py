"""Knowledge index job handler: parse document, write chunks, activate index."""

from __future__ import annotations

import hashlib
import json
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

    Parsing runs outside the transaction; activation and job completion run
    in the same write transaction.
    """
    document_id = job_payload["document_id"]
    version = job_payload["version"]
    file_path = job_payload["file_path"]

    # Heavy work outside the DB transaction
    text = read_document(file_path)
    chunks = split_text(text, document_id=document_id)

    chunk_inputs = [
        {
            "chunk_no": chunk.order,
            "text": chunk.text,
            "locator": {"chunk_id": chunk.chunk_id, "order": chunk.order},
        }
        for chunk in chunks
    ]

    artifact_payload = {
        "document_id": document_id,
        "version": version,
        "parser_version": PARSER_VERSION,
        "embedding_model_version": EMBEDDING_MODEL_VERSION,
        "chunks": chunk_inputs,
    }
    artifact_bytes = json.dumps(
        artifact_payload, ensure_ascii=False, sort_keys=True
    ).encode("utf-8")
    artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()
    artifact_path = _persist_artifact(store, document_id, version, artifact_bytes)

    with store.write() as uow:
        index_info = uow.knowledge.begin_index(
            document_id=document_id,
            version=version,
            job_id=_lease_field(lease, "job_id"),
            parser_version=PARSER_VERSION,
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lease=lease,
        )
        index_id = index_info["id"]

        write_result = uow.knowledge.write_chunks(index_id, chunk_inputs, lease)

        document = uow.knowledge.activate_index(
            document_id=document_id,
            version=version,
            artifact_path=artifact_path,
            artifact_sha256=artifact_sha256,
            expected_chunk_count=len(chunks),
            lease=lease,
        )

        uow.jobs.complete_job(
            lease,
            {"document_id": document_id, "index_version": version},
            now,
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


def _persist_artifact(
    store: Any, document_id: str, version: str, artifact_bytes: bytes
) -> str:
    """Persist index artifact through C store when possible.

    Returns relative path. Falls back to a logical path for fake stores.
    """
    source_id = None
    try:
        with store.read() as reader:
            doc = reader.knowledge.get_chunks(document_id)
            source_id = doc.get("source_id") if isinstance(doc, dict) else None
    except (KeyError, AttributeError, TypeError):
        source_id = None

    if source_id is not None and hasattr(store, "persist_file"):
        import io

        name = f"index-{version}.json"
        asset = store.persist_file(
            source_id=source_id,
            original_name=name,
            stream=io.BytesIO(artifact_bytes),
        )
        return asset["relative_path"]

    return f"indices/{document_id}/{version}.json"


def _lease_field(lease: Any, field: str) -> Any:
    if isinstance(lease, dict):
        return lease[field]
    return getattr(lease, field)
