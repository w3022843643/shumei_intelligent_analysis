"""Stable service entry points consumed by the API layer.

These functions intentionally expose service-level operations rather than HTTP
concepts. The FastAPI layer is responsible for authentication, request parsing,
and response serialization.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

MODULE_VERSION = "0.1.0"


def health() -> dict[str, str]:
    """Return a lightweight module health marker."""
    return {"module": "intelligent_analysis", "version": MODULE_VERSION, "status": "ready"}


def answer_message(
    message: str,
    conversation_id: UUID | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Answer a user question with metric evidence and document citations."""
    raise NotImplementedError("RAG assistant is not implemented yet")


def index_document(file_path: str, metadata: dict[str, Any]) -> dict[str, Any]:
    """Parse and index an authorized knowledge document."""
    raise NotImplementedError("Knowledge document indexing is not implemented yet")


def analyze_video(video_id: UUID, config: dict[str, Any]) -> dict[str, Any]:
    """Run person detection, tracking, and virtual-line counting on a video."""
    raise NotImplementedError("Video analysis is not implemented yet")


def get_camera_counts(
    video_id: UUID,
    analysis_id: UUID,
    start: str | None = None,
    end: str | None = None,
    interval_minutes: int | None = None,
) -> dict[str, Any]:
    """Return validated entrance count points for an analyzed video."""
    raise NotImplementedError("Camera count query is not implemented yet")


def forecast_short_term(
    video_id: UUID,
    analysis_id: UUID,
    cutoff_at: str,
    horizon_minutes: int,
    step_minutes: int,
    direction: str,
) -> dict[str, Any]:
    """Forecast future entrance or exit counts for one specified entrance."""
    raise NotImplementedError("Short-term forecast is not implemented yet")
