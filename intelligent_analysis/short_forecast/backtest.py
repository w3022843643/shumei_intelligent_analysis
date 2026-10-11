"""Time-ordered backtest helpers."""

from __future__ import annotations

from collections.abc import Sequence


def mean_absolute_error(actual: Sequence[float], predicted: Sequence[float]) -> float:
    if len(actual) != len(predicted) or not actual:
        raise ValueError("actual and predicted must be non-empty and have equal length")
    return sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual)
