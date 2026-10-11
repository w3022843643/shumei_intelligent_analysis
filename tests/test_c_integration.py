"""Real integration test: E AnalysisWorker against a real C SQLite store.

This exercises the actual C package (data_foundation) end to end:
migration -> document registration -> job enqueue -> E worker claim ->
parse/chunk -> begin_index/write_chunks/activate_index -> complete_job.

Requires the C handoff package (alembic dir) on disk; skips if unavailable.
Set C_HANDOFF_DIR to the extracted ``data_foundation`` folder containing
alembic.ini and the alembic/ directory.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

pytest.importorskip("data_foundation")

CANDIDATE_DIRS = [
    os.environ.get("C_HANDOFF_DIR"),
    r"F:\分工与项目\C交接包\data_foundation",
]


def _handoff_dir() -> Path | None:
    for candidate in CANDIDATE_DIRS:
        if candidate and (Path(candidate) / "alembic.ini").exists():
            return Path(candidate)
    return None


pytestmark = pytest.mark.skipif(
    _handoff_dir() is None,
    reason="C handoff package with alembic.ini not found",
)


def _migrate(database_url: str, handoff: Path) -> None:
    env = dict(os.environ)
    env["DATABASE_URL"] = database_url
    env.pop("HTTP_PROXY", None)
    env.pop("HTTPS_PROXY", None)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        cwd=handoff,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_e_worker_indexes_real_document():
    import data_foundation
    from data_foundation import (
        AssetCreate,
        EntityCreate,
        JobCreate,
        MetricCreate,
        SourceCreate,
    )

    from intelligent_analysis.worker import AnalysisWorker

    handoff = _handoff_dir()
    import json

    tmp = tempfile.TemporaryDirectory()
    data_root = Path(tmp.name) / "assets"
    data_root.mkdir()
    db_path = Path(tmp.name) / "test.db"
    database_url = f"sqlite:///{db_path}"

    try:
        _migrate(database_url, handoff)
        store = data_foundation.create_store(
            database_url,
            data_root=data_root,
            allow_sqlite_for_tests=True,
        )

        scenic_id = str(uuid.uuid4())
        source_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        metrics = json.loads(
            (handoff / "assets" / "metric_dictionary.json").read_text(encoding="utf-8")
        )
        with store.write() as w:
            for item in metrics["metrics"]:
                w.catalog.upsert_metric(MetricCreate(**item))
            w.catalog.create_entity(
                EntityCreate(
                    id=scenic_id, name="集成测试景区", type="scenic", region_code="340000"
                )
            )
            w.provenance.register_source(
                SourceCreate(
                    id=source_id,
                    publisher="测试发布方",
                    title="测试来源",
                    url="https://example.invalid",
                    usage_note="集成测试",
                    update_frequency="monthly",
                    native_grain="month",
                    verification_status="verified",
                )
            )

        # Real markdown file on disk, registered as document + asset
        doc_text = "# 黄山开放公告\n\n黄山每日开放时间为早上六点至下午五点。\n\n索道运行至下午四点半。\n".encode()
        staged = store.persist_file(
            source_id=source_id,
            original_name="notice.md",
            stream=io.BytesIO(doc_text),
        )
        with store.write() as w:
            asset = w.provenance.register_asset(
                AssetCreate(
                    source_id=source_id,
                    url="https://example.invalid/notice.md",
                    title="黄山开放公告",
                    retrieved_at=now,
                    published_at=now,
                    media_type="text/markdown",
                    usage_note="集成测试",
                    **staged,
                )
            )
            document = w.knowledge.register_document(
                {
                    "source_id": source_id,
                    "asset_id": asset["id"],
                    "title": "黄山开放公告",
                    "publisher": "测试发布方",
                    "source_url": "https://example.invalid/notice.md",
                    "published_at": now,
                    "valid_from": None,
                    "valid_until": None,
                    "permission_note": "集成测试授权",
                    "document_version": "v1",
                },
                [scenic_id],
            )
            file_path = str(data_root / asset["relative_path"])
            job = w.jobs.enqueue_or_get(
                JobCreate(
                    "knowledge_index",
                    uuid.uuid4().hex,
                    {
                        "document_id": document["id"],
                        "version": "v1",
                        "file_path": file_path,
                    },
                    "集成测试索引",
                ),
                now,
            )

        # Run E worker once
        worker = AnalysisWorker(store=store)
        result = worker.run_once()

        assert result is not None
        assert result["chunk_count"] >= 1
        assert result["document_index_status"] == "ready"

        with store.read() as r:
            chunks = r.knowledge.get_chunks(document["id"])
            assert chunks["status"] == "ready"
            assert len(chunks["items"]) == result["chunk_count"]
            assert r.jobs.get_job(job["id"])["status"] == "succeeded"

        store.dispose()
    finally:
        tmp.cleanup()
