"""Virtual-line entry and exit counting with entrance-specific direction rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Point = tuple[float, float]
CrossingKind = Literal["entry", "exit"] | None


def orientation(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segments_intersect(a: Point, b: Point, c: Point, d: Point) -> bool:
    o1 = orientation(a, b, c)
    o2 = orientation(a, b, d)
    o3 = orientation(c, d, a)
    o4 = orientation(c, d, b)
    return o1 * o2 < 0 and o3 * o4 < 0


@dataclass
class VirtualLineCounter:
    """Count crossings of one virtual line for one specified entrance.

    Image coordinates use x right and y down. Looking from line point A toward B,
    the left side therefore has negative orientation. If ``entry_side='left'``,
    movement from the right side to the left side is an entry; the reverse is an exit.
    """

    line_start: Point
    line_end: Point
    entry_side: Literal["left", "right"]
    in_count: int = 0
    out_count: int = 0
    _last_positions: dict[str, Point] = field(default_factory=dict)

    def update_track(self, track_id: str, position: Point) -> Literal["entry", "exit"] | None:
        previous = self._last_positions.get(track_id)
        self._last_positions[track_id] = position
        if previous is None:
            return None

        kind = self.classify_crossing(previous, position)
        if kind == "entry":
            self.in_count += 1
        elif kind == "exit":
            self.out_count += 1
        return kind

    def classify_crossing(self, previous: Point, current: Point) -> CrossingKind:
        if not segments_intersect(self.line_start, self.line_end, previous, current):
            return None

        start_side = _sign(orientation(self.line_start, self.line_end, previous))
        end_side = _sign(orientation(self.line_start, self.line_end, current))
        target_side = -1 if self.entry_side == "left" else 1

        if start_side == -target_side and end_side == target_side:
            return "entry"
        if start_side == target_side and end_side == -target_side:
            return "exit"
        return None


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0
