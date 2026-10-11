from pathlib import Path
from uuid import uuid4

from intelligent_analysis.service import (
    analyze_video,
    answer_message,
    get_camera_counts,
    index_document,
    process_document_index,
    reindex_documents,
)


def test_index_document_returns_pending_job(tmp_path: Path):
    doc = tmp_path / "notice.md"
    doc.write_text("# 通知\n景区正常开放。", encoding="utf-8")
    metadata = {
        "title": "开放通知",
        "publisher": "测试单位",
        "source_url": "https://example.com/notice",
        "permission_note": "测试授权",
    }

    result = index_document(str(doc), metadata)

    assert result["document_id"] == "notice"
    assert result["index_status"] == "pending"
    assert result["job_id"]


def test_process_document_index_makes_document_searchable(tmp_path: Path):
    doc = tmp_path / "notice.md"
    doc.write_text("黄山开放时间为六点。", encoding="utf-8")
    metadata = {
        "title": "开放通知",
        "publisher": "测试单位",
        "permission_note": "测试授权",
    }

    process_result = process_document_index(str(doc), metadata)
    answer = answer_message("黄山几点开放？")

    assert process_result["index_status"] == "ready"
    assert process_result["chunk_count"] == 1
    assert answer["status"] == "answered"
    assert answer["citations"][0]["date"] is None
    assert answer["used_metric_queries"] == []


def test_reindex_documents_returns_pending_count():
    result = reindex_documents(["doc-1", "doc-2"], "更新索引")

    assert result["pending_count"] == 2
    assert result["job_id"]


def test_analyze_video_returns_complete_config():
    result = analyze_video(
        uuid4(),
        {
            "detector_model_version": "yolov8n-test",
            "openvino_version": "2025.4",
            "device": "CPU",
            "count_line": {"x1": 0, "y1": 0.5, "x2": 1, "y2": 0.5},
            "entry_side": "right",
            "interval_minutes": 15,
        },
    )

    assert result["status"] == "queued"
    assert result["config"]["interval_minutes"] == 15
    assert result["analysis_id"]


def test_counts_response_includes_analysis_id():
    analysis_id = uuid4()
    result = get_camera_counts(uuid4(), analysis_id)

    assert result["analysis_id"] == str(analysis_id)
    assert result["status"] == "analysis_not_ready"
