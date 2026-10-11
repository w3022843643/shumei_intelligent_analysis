"""Video analysis job handler: detect, track, count crossings, write results."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..contracts import VideoAnalysisConfig


@dataclass
class VideoPipelineResult:
    """Result of processing one video analysis job."""

    analysis_id: str
    window_count: int
    points: list[dict[str, Any]] = field(default_factory=list)
    manual_validation: dict[str, Any] | None = None
    status: str = "succeeded"
    reason: str | None = None


def process_video_job(
    store: Any,
    job_payload: dict[str, Any],
    lease: Any,
    now: Any,
    detector: Callable[[Any], list[tuple[float, float, float, float]]] | None = None,
) -> dict[str, Any]:
    """Process a video_analysis job against C store.

    Expected job payload:
    - analysis_id: str
    - video_id: str
    - file_path: str (staged video)
    - recorded_start_at: ISO datetime
    - config: dict matching VideoAnalysisConfig

    If detector is None (no YOLO model loaded), returns analysis_not_ready
    without writing counts.
    """
    analysis_id = job_payload["analysis_id"]
    config_data = job_payload["config"]

    VideoAnalysisConfig.model_validate(config_data)

    with store.write() as uow:
        if detector is None:
            uow.jobs.heartbeat(lease, now)
            return {
                "analysis_id": analysis_id,
                "status": "analysis_not_ready",
                "reason": "No YOLO detector configured; video processing skipped.",
                "window_count": 0,
            }

        # Real frame processing pipeline:
        # 1. Read frames via RecordedVideoReader
        # 2. Run detector on each frame → bboxes
        # 3. Run CentroidTracker on bboxes → track IDs
        # 4. For each track, check VirtualLineCounter crossing
        # 5. Aggregate into windows, write via uow.video.write_counts()
        # 6. Call uow.video.complete_analysis()

        return {
            "analysis_id": analysis_id,
            "status": "analysis_not_ready",
            "reason": "Video pipeline structure defined but frame processing not yet connected.",
            "window_count": 0,
        }


def build_count_input(
    window_start: datetime,
    window_end: datetime,
    entries: int,
    exits: int,
    quality_status: str = "verified",
) -> dict[str, Any]:
    """Build a CountInput-compatible dict for C store."""
    return {
        "window_start": window_start,
        "window_end": window_end,
        "entries": entries,
        "exits": exits,
        "quality_status": quality_status,
    }
