"""Simple persistence baseline for short-term counts."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta


def naive_baseline(
    history: Sequence[float], horizon_steps: int, step_minutes: int, cutoff: datetime
):
    if not history:
        raise ValueError("history must not be empty")
    value = float(history[-1])
    return [
        (cutoff + timedelta(minutes=step_minutes * (index + 1)), value)
        for index in range(horizon_steps)
    ]
