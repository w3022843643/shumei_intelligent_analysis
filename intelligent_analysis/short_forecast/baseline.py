"""Baseline models for short-term entrance counts."""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from datetime import datetime, timedelta

from ..contracts import ForecastPoint

MIN_HISTORY_POINTS = 4


def naive_baseline(
    history: Sequence[float], horizon_steps: int, step_minutes: int, cutoff: datetime
) -> list[tuple[datetime, float]]:
    if not history:
        raise ValueError("history must not be empty")
    value = float(history[-1])
    return _future_times(cutoff, horizon_steps, step_minutes, value)


def forecast_from_history(
    history: Sequence[tuple[datetime, float]],
    cutoff: datetime,
    horizon_minutes: int,
    step_minutes: int,
) -> tuple[list[ForecastPoint], dict[str, float]]:
    if horizon_minutes % step_minutes != 0:
        raise ValueError("horizon_minutes must be divisible by step_minutes")
    horizon_steps = horizon_minutes // step_minutes
    ordered = sorted(history, key=lambda item: item[0])
    values = [float(value) for _, value in ordered]

    if len(values) < MIN_HISTORY_POINTS:
        raise ValueError("at least four history points are required")

    recent_window = values[-min(3, len(values)) :]
    forecast_value = statistics.mean(recent_window)
    residuals = [abs(values[index] - values[index - 1]) for index in range(1, len(values))]
    margin = statistics.mean(residuals) if residuals else 0.0

    points = [
        ForecastPoint(
            target_time=cutoff + timedelta(minutes=step_minutes * index),
            value=forecast_value,
            lower=max(0.0, forecast_value - margin),
            upper=forecast_value + margin,
        )
        for index in range(1, horizon_steps + 1)
    ]
    validation = {"mae": statistics.mean(abs(r) for r in residuals), "residual_margin": margin}
    return points, validation


def _future_times(
    cutoff: datetime, horizon_steps: int, step_minutes: int, value: float
) -> list[tuple[datetime, float]]:
    return [
        (cutoff + timedelta(minutes=step_minutes * (index + 1)), value)
        for index in range(horizon_steps)
    ]
