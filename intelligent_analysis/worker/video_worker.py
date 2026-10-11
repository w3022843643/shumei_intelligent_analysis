"""Video analysis job handler: detect, track, count crossings, write results."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from ..contracts import VideoAnalysisConfig
from ..vision.line_counter import VirtualLineCounter
from ..vision.tracker import CentroidTracker


@dataclass
class FrameData:
    """One frame from a video source."""

    frame_index: int
    timestamp_seconds: float
    frame: Any


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
    - frame_width, frame_height: int
    - config: dict matching VideoAnalysisConfig

    Raises RuntimeError if no detector is configured so the runner fails this
    job (rather than the whole worker exiting).
    """
    analysis_id = job_payload["analysis_id"]
    video_id = job_payload["video_id"]
    config_data = job_payload["config"]
    config = VideoAnalysisConfig.model_validate(config_data)

    if detector is None:
        raise RuntimeError("No YOLO detector configured; video analysis cannot run.")

    recorded_start = datetime.fromisoformat(job_payload["recorded_start_at"])
    frame_width = int(job_payload["frame_width"])
    frame_height = int(job_payload["frame_height"])
    file_path = job_payload["file_path"]

    # Inference outside the DB transaction
    frames = _read_video_frames(file_path)
    window_dicts = process_frame_sequence(
        frames=frames,
        detector=detector,
        config=config,
        frame_width=frame_width,
        frame_height=frame_height,
        recorded_start=recorded_start,
    )

    points = [_to_count_input(w) for w in window_dicts]

    with store.write() as uow:
        uow.video.write_counts(analysis_id, points, lease)
        uow.video.complete_analysis(analysis_id, len(points), lease)
        uow.jobs.complete_job(lease, {"analysis_id": analysis_id}, now)

    return {
        "analysis_id": analysis_id,
        "video_id": video_id,
        "status": "succeeded",
        "window_count": len(points),
        "points": window_dicts,
    }


def process_frame_sequence(
    frames: Iterable[FrameData],
    detector: Callable[[Any], list[tuple[float, float, float, float]]],
    config: VideoAnalysisConfig,
    frame_width: int,
    frame_height: int,
    recorded_start: datetime,
) -> list[dict[str, Any]]:
    """Run detection, tracking, and line counting over a frame sequence.

    Returns count-window dicts for complete time windows. Centroids are
    normalized to 0—1 before feeding the virtual line counter.
    """
    line = config.count_line
    tracker = CentroidTracker()
    counter = VirtualLineCounter(
        line_start=(line.x1, line.y1),
        line_end=(line.x2, line.y2),
        entry_side=config.entry_side,
    )

    interval = timedelta(minutes=config.interval_minutes)
    current_window_start = recorded_start
    window_entries = 0
    window_exits = 0
    windows: list[dict[str, Any]] = []

    for frame_data in frames:
        timestamp = recorded_start + timedelta(seconds=frame_data.timestamp_seconds)

        while timestamp >= current_window_start + interval:
            windows.append(
                build_count_input(
                    current_window_start,
                    current_window_start + interval,
                    window_entries,
                    window_exits,
                )
            )
            current_window_start += interval
            window_entries = 0
            window_exits = 0

        bboxes = detector(frame_data.frame)
        tracks = tracker.update(list(bboxes), frame_index=frame_data.frame_index)

        for track_id, track in tracks.items():
            cx, cy = track.centroid
            normalized = (cx / frame_width, cy / frame_height)
            kind = counter.update_track(str(track_id), normalized)
            if kind == "entry":
                window_entries += 1
            elif kind == "exit":
                window_exits += 1

    return windows


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


def _to_count_input(window: dict[str, Any]) -> Any:
    """Convert window dict to C CountInput dataclass; pass dict through for fakes."""
    try:
        from data_foundation import CountInput

        return CountInput(
            window_start=window["window_start"],
            window_end=window["window_end"],
            entries=window["entries"],
            exits=window["exits"],
            quality_status=window["quality_status"],
        )
    except ImportError:
        return window


def _read_video_frames(file_path: str) -> Iterable[FrameData]:
    """Open recorded video and yield frames via OpenCV."""
    from ..vision.video_reader import RecordedVideoReader

    with RecordedVideoReader(file_path) as reader:
        yield from reader.frames()
