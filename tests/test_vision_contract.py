from uuid import uuid4

from intelligent_analysis.service import analyze_video, forecast_short_term, get_camera_counts


def test_video_analysis_job_accepts_valid_config():
    config = {
        "detector_model_version": "yolov8n-2026.10",
        "openvino_version": "2025.4",
        "device": "CPU",
        "count_line": {"x1": 0.1, "y1": 0.2, "x2": 0.9, "y2": 0.2},
        "entry_side": "left",
        "interval_minutes": 5,
    }

    result = analyze_video(uuid4(), config)

    assert result["status"] == "queued"
    assert result["inference_engine"] == "openvino"
    assert result["analysis_id"]


def test_counts_returns_not_ready_before_worker_connected():
    result = get_camera_counts(uuid4(), uuid4())

    assert result["status"] == "analysis_not_ready"
    assert result["points"] == []


def test_forecast_returns_data_insufficient_without_counts():
    result = forecast_short_term(
        video_id=uuid4(),
        analysis_id=uuid4(),
        cutoff_at="2026-10-11T10:00:00+08:00",
        horizon_minutes=30,
        step_minutes=5,
        direction="entries",
    )

    assert result["status"] == "data_insufficient"
    assert result["forecast_points"] == []
