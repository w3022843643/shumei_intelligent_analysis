"""Tests for E worker dispatch and job handling."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from intelligent_analysis.contracts import VideoAnalysisConfig
from intelligent_analysis.worker import AnalysisWorker
from intelligent_analysis.worker.knowledge_worker import process_knowledge_job
from intelligent_analysis.worker.video_worker import (
    FrameData,
    build_count_input,
    process_frame_sequence,
    process_video_job,
)


class FakeLease:
    def __init__(self, job_id="job-1", attempt_no=1, lease_token="token-1"):
        self.job_id = job_id
        self.attempt_no = attempt_no
        self.lease_token = lease_token


class FakeKnowledgeRepo:
    def __init__(self):
        self.begin_index_calls = []
        self.write_chunks_calls = []
        self.activate_calls = []

    def begin_index(self, **kwargs):
        self.begin_index_calls.append(kwargs)
        return {"id": "index-1", "document_id": kwargs["document_id"]}

    def write_chunks(self, index_id, chunks, lease):
        self.write_chunks_calls.append((index_id, chunks, lease))
        return {"inserted": len(chunks), "skipped": 0}

    def activate_index(self, **kwargs):
        self.activate_calls.append(kwargs)
        return {"index_status": "ready", "row_version": 2}


class FakeJobsRepo:
    def __init__(self):
        self.complete_calls = []
        self.fail_calls = []
        self.heartbeat_calls = []

    def heartbeat(self, lease, now):
        self.heartbeat_calls.append((lease, now))

    def complete_job(self, lease, result, now):
        self.complete_calls.append((lease, result, now))
        return {"status": "succeeded"}

    def fail_job(self, lease, error_summary, now):
        self.fail_calls.append((lease, error_summary, now))
        return {"status": "failed"}


class FakeVideoRepo:
    def __init__(self):
        self.write_counts_calls = []
        self.complete_calls = []

    def write_counts(self, analysis_id, points, lease):
        self.write_counts_calls.append((analysis_id, points, lease))
        return {"inserted": len(points), "skipped": 0}

    def complete_analysis(self, analysis_id, expected_window_count, lease, manual_validation=None):
        self.complete_calls.append((analysis_id, expected_window_count, lease))
        return {"status": "succeeded"}


class FakeUow:
    def __init__(self, knowledge=None, jobs=None, video=None):
        self.knowledge = knowledge or FakeKnowledgeRepo()
        self.jobs = jobs or FakeJobsRepo()
        self.video = video or FakeVideoRepo()


class FakeStore:
    def __init__(self, uow):
        self._uow = uow

    def write(self):
        class Ctx:
            def __init__(self, uow):
                self.uow = uow

            def __enter__(self):
                return self.uow

            def __exit__(self, *args):
                pass

        return Ctx(self._uow)


def test_knowledge_job_calls_begin_write_activate(tmp_path):
    doc = tmp_path / "notice.md"
    doc.write_text("# 通知\n黄山景区正常开放。", encoding="utf-8")

    uow = FakeUow()
    store = FakeStore(uow)
    lease = FakeLease()
    now = datetime.now(UTC)

    result = process_knowledge_job(
        store=store,
        job_payload={
            "document_id": "doc-1",
            "version": "v1",
            "file_path": str(doc),
        },
        lease=lease,
        now=now,
    )

    assert result["chunk_count"] >= 1
    assert result["document_index_status"] == "ready"
    assert len(uow.knowledge.begin_index_calls) == 1
    assert len(uow.knowledge.write_chunks_calls) == 1
    assert len(uow.knowledge.activate_calls) == 1


def test_video_job_without_detector_returns_not_ready():
    uow = FakeUow()
    store = FakeStore(uow)
    lease = FakeLease(job_id="job-video-1")
    now = datetime.now(UTC)

    result = process_video_job(
        store=store,
        job_payload={
            "analysis_id": "analysis-1",
            "video_id": "video-1",
            "file_path": "/fake/video.mp4",
            "recorded_start_at": "2026-10-11T08:00:00+08:00",
            "config": {
                "detector_model_version": "yolov8n",
                "openvino_version": "2025.4",
                "device": "CPU",
                "count_line": {"x1": 0, "y1": 0.5, "x2": 1, "y2": 0.5},
                "entry_side": "right",
                "interval_minutes": 5,
            },
        },
        lease=lease,
        now=now,
        detector=None,
    )

    assert result["status"] == "analysis_not_ready"
    assert result["window_count"] == 0


def test_build_count_input():
    start = datetime(2026, 10, 11, 8, 0, tzinfo=UTC)
    end = start + timedelta(minutes=5)

    result = build_count_input(start, end, entries=12, exits=4)

    assert result["entries"] == 12
    assert result["exits"] == 4
    assert result["quality_status"] == "verified"


def test_runner_dispatches_knowledge_job():
    uow = FakeUow()
    store = FakeStore(uow)

    # Override claim_job to return a knowledge job
    class ClaimJobsRepo(FakeJobsRepo):
        def claim_job(self, worker_id, now, lease_seconds=120):
            return {
                "job": {
                    "id": "job-1",
                    "type": "knowledge_index",
                    "payload": {
                        "document_id": "doc-1",
                        "version": "v1",
                        "file_path": "nonexistent.md",
                    },
                },
                "lease": {"job_id": "job-1", "attempt_no": 1, "lease_token": "tok"},
            }

    uow.jobs = ClaimJobsRepo()
    worker = AnalysisWorker(store=store)

    # This will fail on nonexistent file, but should call fail_job
    result = worker.run_once()

    assert result["status"] == "failed"
    assert len(uow.jobs.fail_calls) == 1


def test_runner_returns_none_when_no_jobs():
    class NoJobRepo(FakeJobsRepo):
        def claim_job(self, worker_id, now, lease_seconds=120):
            return None

    uow = FakeUow()
    uow.jobs = NoJobRepo()
    store = FakeStore(uow)
    worker = AnalysisWorker(store=store)

    result = worker.run_once()

    assert result is None


def _make_video_config():
    return VideoAnalysisConfig.model_validate(
        {
            "detector_model_version": "yolov8n-test",
            "openvino_version": "2025.4",
            "device": "CPU",
            "count_line": {"x1": 0, "y1": 0.5, "x2": 1, "y2": 0.5},
            "entry_side": "left",
            "interval_minutes": 1,
        }
    )


def test_process_frame_sequence_counts_entry():
    recorded_start = datetime(2026, 10, 11, 8, 0, tzinfo=UTC)
    config = _make_video_config()

    fps = 1
    frame_count = 61

    def fake_detector(frame_index):
        cy = 340 - (280 * frame_index // (frame_count - 1))
        return [(100, cy - 20, 140, cy + 20)]

    frames = [
        FrameData(frame_index=i, timestamp_seconds=i / fps, frame=i)
        for i in range(frame_count)
    ]

    windows = process_frame_sequence(
        frames=frames,
        detector=fake_detector,
        config=config,
        frame_width=640,
        frame_height=400,
        recorded_start=recorded_start,
    )

    total_entries = sum(w["entries"] for w in windows)
    total_exits = sum(w["exits"] for w in windows)
    assert total_entries == 1
    assert total_exits == 0


def test_process_video_job_with_detector_writes_counts():
    recorded_start = datetime(2026, 10, 11, 8, 0, tzinfo=UTC)

    # Build a complete fake store with video repo accepting writes
    class FakeVideoWriteRepo:
        def __init__(self):
            self.write_counts_calls = []
            self.complete_calls = []

        def write_counts(self, analysis_id, points, lease):
            self.write_counts_calls.append((analysis_id, points))
            return {"inserted": len(points), "skipped": 0}

        def complete_analysis(self, analysis_id, expected_window_count, lease, manual_validation=None):
            self.complete_calls.append((analysis_id, expected_window_count))
            return {"status": "succeeded"}

    video_repo = FakeVideoWriteRepo()
    uow = FakeUow(video=video_repo)
    store = FakeStore(uow)

    fps = 1
    frame_count = 61

    def fake_detector(frame_index):
        cy = 340 - (280 * frame_index // (frame_count - 1))
        return [(100, cy - 20, 140, cy + 20)]

    # Override _read_video_frames by monkeypatching via payload file_path
    import intelligent_analysis.worker.video_worker as vw

    def fake_read(_path):
        for i in range(frame_count):
            yield FrameData(frame_index=i, timestamp_seconds=i / fps, frame=i)

    original = vw._read_video_frames
    vw._read_video_frames = fake_read
    try:
        result = process_video_job(
            store=store,
            job_payload={
                "analysis_id": "analysis-1",
                "video_id": "video-1",
                "file_path": "fake.mp4",
                "recorded_start_at": recorded_start.isoformat(),
                "frame_width": 640,
                "frame_height": 400,
                "config": {
                    "detector_model_version": "yolov8n-test",
                    "openvino_version": "2025.4",
                    "device": "CPU",
                    "count_line": {"x1": 0, "y1": 0.5, "x2": 1, "y2": 0.5},
                    "entry_side": "left",
                    "interval_minutes": 1,
                },
            },
            lease=FakeLease(),
            now=datetime.now(UTC),
            detector=fake_detector,
        )
    finally:
        vw._read_video_frames = original

    assert result["status"] == "succeeded"
    assert result["window_count"] >= 1
    assert len(video_repo.write_counts_calls) == 1
    assert len(video_repo.complete_calls) == 1
