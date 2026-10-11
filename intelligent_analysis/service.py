"""Stable service entry points consumed by the API layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from .agent.orchestrator import answer_with_index
from .contracts import (
    ChatResponse,
    DocumentMetadata,
    ForecastResponse,
    IndexAccepted,
    JobAccepted,
    ReindexAccepted,
    VideoAnalysisConfig,
)
from .knowledge.chunk import split_text
from .knowledge.index import InMemoryKnowledgeIndex
from .knowledge.parse import read_document
from .short_forecast.baseline import forecast_from_history

MODULE_VERSION = "0.4.0"
MODEL_VERSION = "short-forecast-rolling-0.2.0"
_global_index = InMemoryKnowledgeIndex()


def health() -> dict[str, str]:
    return {"module": "intelligent_analysis", "version": MODULE_VERSION, "status": "ready"}


def answer_message(
    message: str,
    conversation_id: UUID | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response: ChatResponse = answer_with_index(message, _global_index, conversation_id)
    return response.model_dump(mode="json")


def index_document(file_path: str, metadata: dict[str, Any]) -> dict[str, Any]:
    document_metadata = DocumentMetadata.model_validate(metadata)
    document_id = Path(file_path).stem
    accepted = IndexAccepted(document_id=document_id, job_id=uuid4())
    result = accepted.model_dump(mode="json")
    result["staged_file_path"] = file_path
    result["metadata"] = document_metadata.model_dump(mode="json")
    return result


def process_document_index(file_path: str, metadata: dict[str, Any]) -> dict[str, Any]:
    """Worker operation: parse and index PDF/TXT/MD documents."""
    document_metadata = DocumentMetadata.model_validate(metadata)
    document_id = Path(file_path).stem
    text = read_document(file_path)
    chunks = split_text(text, document_id=document_id)
    _global_index.add_document(document_id, document_metadata, chunks)
    return {
        "document_id": document_id,
        "index_status": "ready",
        "chunk_count": len(chunks),
    }


def reindex_documents(document_ids: list[str], reason: str) -> dict[str, Any]:
    if not 1 <= len(document_ids) <= 100:
        raise ValueError("document_ids must contain 1—100 items")
    if not reason.strip():
        raise ValueError("reason is required")
    accepted = ReindexAccepted(pending_count=len(document_ids))
    return accepted.model_dump(mode="json")


def save_knowledge_index(path: str) -> None:
    _global_index.save(path)


def load_knowledge_index(path: str) -> None:
    global _global_index
    _global_index = InMemoryKnowledgeIndex.load(path)


def analyze_video(video_id: UUID, config: dict[str, Any]) -> dict[str, Any]:
    validated_config = VideoAnalysisConfig.model_validate(config)
    accepted = JobAccepted(job_id=uuid4(), analysis_id=uuid4())
    result = accepted.model_dump(mode="json")
    result["video_id"] = str(video_id)
    result["config"] = validated_config.model_dump(mode="json")
    return result


def get_camera_counts(
    video_id: UUID,
    analysis_id: UUID,
    start: str | None = None,
    end: str | None = None,
    interval_minutes: int | None = None,
) -> dict[str, Any]:
    return {
        "analysis_id": str(analysis_id),
        "status": "analysis_not_ready",
        "points": [],
        "manual_validation": None,
    }


def forecast_short_term(
    video_id: UUID,
    analysis_id: UUID,
    cutoff_at: str,
    horizon_minutes: int,
    step_minutes: int,
    direction: str,
) -> dict[str, Any]:
    response = ForecastResponse(
        status="data_insufficient",
        model_version=MODEL_VERSION,
        reason="No validated camera count history is available before the requested cutoff.",
    )
    return response.model_dump(mode="json")


def forecast_from_count_history(
    history: list[tuple[Any, float]],
    cutoff_at: Any,
    horizon_minutes: int,
    step_minutes: int,
) -> dict[str, Any]:
    points, validation = forecast_from_history(
        history=history,
        cutoff=cutoff_at,
        horizon_minutes=horizon_minutes,
        step_minutes=step_minutes,
    )
    response = ForecastResponse(
        status="ready",
        forecast_points=points,
        training_cutoff=cutoff_at,
        model_version=MODEL_VERSION,
        validation_error=validation["mae"],
    )
    return response.model_dump(mode="json")
