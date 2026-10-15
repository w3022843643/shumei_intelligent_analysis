from datetime import UTC, datetime
from uuid import uuid4

import pytest

from intelligent_analysis import ServiceBindings, configure_services
from intelligent_analysis.integration import DependencyUnavailable, UnsupportedAnalysis
from intelligent_analysis.service import (
    analyze_video,
    answer_message,
    index_document,
    process_document_index,
    reindex_documents,
)

METADATA = {"title": "公告", "publisher": "测试", "permission_note": "测试授权"}


def test_no_phantom_pending_jobs(tmp_path, config):
    metadata = {**METADATA, "document_id": str(uuid4()), "document_version": "v1"}
    with pytest.raises(DependencyUnavailable):
        index_document(str(tmp_path / "notice.md"), metadata)
    with pytest.raises(DependencyUnavailable):
        reindex_documents([metadata["document_id"]], "更新")
    with pytest.raises(UnsupportedAnalysis):
        analyze_video(uuid4(), config)


def test_real_submit_ids_are_preserved(config):
    job, analysis, video = uuid4(), uuid4(), uuid4()
    calls = []

    def submit(kind, payload):
        calls.append((kind, payload))
        return {"job_id": str(job), "analysis_id": str(analysis), "status": "queued"}

    configure_services(ServiceBindings(submit_job=submit, validate_analysis=lambda c: None))
    result = analyze_video(video, config)
    assert result["job_id"] == str(job)
    assert result["analysis_id"] == str(analysis)
    assert result["count_metric"] == "camera_visible_people"
    assert calls[0][0] == "video_analysis"


def test_source_document_version_survives_metadata_validation(tmp_path):
    calls = []
    configure_services(ServiceBindings(submit_job=lambda kind, payload:
        calls.append(payload) or {"job_id": str(uuid4()), "status": "queued"}))
    metadata = {**METADATA, "document_id": str(uuid4()), "document_version": "source-v1"}
    index_document(str(tmp_path / "source.txt"), metadata)
    assert calls[0]["document_version"] == "source-v1"


def test_document_identity_and_expiration(tmp_path):
    path = tmp_path / "misleading-filename.md"
    path.write_text("黄山春节开放时间六点。", encoding="utf-8")
    with pytest.raises(ValueError, match="document_id"):
        process_document_index(str(path), METADATA)
    metadata = {**METADATA, "document_id": "c-id", "valid_until": "2025-02-01T00:00:00Z"}
    process_document_index(str(path), metadata)
    answer = answer_message("黄山春节开放", context={"as_of": datetime(2026, 10, 14, tzinfo=UTC)})
    assert answer["citations"][0]["id"] == "c-id"
    assert "历史资料" in answer["answer"]


def test_numeric_tool_requires_provenance():
    query = {"entity_id": "airport", "metric": "airport_passengers"}
    assert answer_message("多少人", context={"metric_query": query})["status"] == "metric_tool_unavailable"
    with pytest.raises(ValueError, match="provenance"):
        answer_message("多少人", context={"metric_query": query, "metric_tool": lambda q: {"value": 10}})
    data = {"metric": "airport_passengers", "value": 10, "source_ids": ["official"],
            "period_start": "2025-01-01", "period_end": "2025-02-01", "queried_at": "2026-10-14"}
    answer = answer_message("多少人", context={"metric_query": query, "metric_tool": lambda q: data})
    assert answer["metric_result"] == data
    assert answer["citations"][0]["type"] == "metric"
    assert answer["citations"][0]["url"] is None
    assert answer["citations"][0]["date"] is None
