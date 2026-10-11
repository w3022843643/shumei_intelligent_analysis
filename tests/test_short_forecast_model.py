from datetime import datetime, timedelta, timezone

from intelligent_analysis.service import forecast_from_count_history
from intelligent_analysis.short_forecast.backtest import walk_forward_persistence


def test_forecast_from_count_history_returns_points():
    tz = timezone(timedelta(hours=8))
    cutoff = datetime(2026, 10, 11, 10, 0, tzinfo=tz)
    history = [
        (cutoff - timedelta(minutes=20), 2.0),
        (cutoff - timedelta(minutes=15), 4.0),
        (cutoff - timedelta(minutes=10), 3.0),
        (cutoff - timedelta(minutes=5), 5.0),
    ]

    result = forecast_from_count_history(history, cutoff, 30, 5)

    assert result["status"] == "ready"
    assert len(result["forecast_points"]) == 6
    assert result["training_cutoff"]
    assert result["validation_error"] is not None
    assert result["forecast_points"][0]["lower"] <= result["forecast_points"][0]["upper"]


def test_walk_forward_persistence():
    result = walk_forward_persistence([1, 2, 3, 4, 5], minimum_train=3)

    assert result["sample_count"] == 2
    assert result["mae"] == 1.0
