"""E worker runner: claims jobs from C store and dispatches to handlers."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .knowledge_worker import process_knowledge_job
from .video_worker import process_video_job

logger = logging.getLogger(__name__)


@dataclass
class WorkerConfig:
    worker_id: str = "e-analysis-worker"
    lease_seconds: int = 120
    poll_interval_seconds: float = 2.0
    job_types: tuple[str, ...] = ("knowledge_index", "video_analysis", "short_forecast")


class AnalysisWorker:
    """Claims E-type jobs from C store and runs the appropriate handler.

    The C store is injected by D; this worker never imports C directly.
    """

    def __init__(
        self,
        store: Any,
        config: WorkerConfig | None = None,
        detector: Callable[[Any], list[tuple[float, float, float, float]]] | None = None,
    ) -> None:
        self.store = store
        self.config = config or WorkerConfig()
        self.detector = detector
        self._running = False

    def run_once(self) -> dict[str, Any] | None:
        """Claim one job and process it. Returns result dict or None if no job."""
        now = datetime.now(UTC)

        with self.store.write() as uow:
            claimed = uow.jobs.claim_job(
                worker_id=self.config.worker_id,
                now=now,
                lease_seconds=self.config.lease_seconds,
            )

        if claimed is None:
            return None

        job = claimed["job"]
        lease = claimed["lease"]
        job_type = job["type"]
        payload = job.get("payload", {})

        logger.info("Claimed job %s (type=%s, id=%s)", lease["job_id"], job_type, job["id"])

        try:
            result = self._dispatch(job_type, payload, lease, now)
            with self.store.write() as uow:
                uow.jobs.complete_job(lease, result, now=datetime.now(UTC))
            logger.info("Completed job %s", lease["job_id"])
            return result
        except Exception as exc:
            logger.exception("Job %s failed", lease["job_id"])
            error_summary = f"{type(exc).__name__}: {exc}"[:2000]
            with self.store.write() as uow:
                uow.jobs.fail_job(lease, error_summary, now=datetime.now(UTC))
            return {"status": "failed", "error": error_summary}

    def _dispatch(
        self,
        job_type: str,
        payload: dict[str, Any],
        lease: Any,
        now: datetime,
    ) -> dict[str, Any]:
        if job_type == "knowledge_index":
            return process_knowledge_job(self.store, payload, lease, now)
        if job_type == "video_analysis":
            return process_video_job(self.store, payload, lease, now, detector=self.detector)
        if job_type == "short_forecast":
            # Forecast is triggered from API layer, not background worker.
            # If a forecast job is enqueued, return not ready.
            return {
                "status": "data_insufficient",
                "reason": "Short forecast jobs should be processed synchronously via API.",
            }
        raise ValueError(f"Unknown job type: {job_type}")

    def start(self) -> None:
        """Blocking poll loop. Use Ctrl+C to stop."""
        import time

        self._running = True
        logger.info("E worker started, polling for %s", self.config.job_types)
        while self._running:
            self.run_once()
            time.sleep(self.config.poll_interval_seconds)

    def stop(self) -> None:
        self._running = False
