"""E-side end-to-end demo using synthetic data.

Runs without real documents, videos, or models. Demonstrates:
1. Knowledge pipeline: parse → chunk → index → answer with citations
2. Vision pipeline: synthetic detections → track → cross line → counts
3. Forecast pipeline: synthetic count history → forecast with intervals

Usage:
    python demo/end_to_end_demo.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

# Ensure package is importable when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from intelligent_analysis.agent.orchestrator import answer_with_index
from intelligent_analysis.contracts import DocumentMetadata
from intelligent_analysis.knowledge.chunk import split_text
from intelligent_analysis.knowledge.index import InMemoryKnowledgeIndex
from intelligent_analysis.short_forecast.backtest import walk_forward_persistence
from intelligent_analysis.short_forecast.baseline import forecast_from_history
from intelligent_analysis.vision.line_counter import VirtualLineCounter
from intelligent_analysis.vision.tracker import CentroidTracker
from intelligent_analysis.vision.validation import CountWindow, validate_counts


def demo_knowledge_pipeline() -> None:
    print("=" * 60)
    print("1. RAG KNOWLEDGE PIPELINE")
    print("=" * 60)

    synthetic_doc = """# 黄山风景区开放公告

黄山风景区每日开放时间为早上六点至下午五点。
门票价格为旺季一百九十元，淡季一百五十元。
景区内索道运行时间为早上六点半至下午四点半。
如遇恶劣天气，部分景点可能临时关闭。
"""

    metadata = DocumentMetadata(
        title="黄山风景区开放公告",
        publisher="黄山风景区管理委员会",
        source_url="https://example.com/notice",
        published_at=datetime(2026, 9, 1, 9, 0, tzinfo=UTC),
        permission_note="演示用合成文档",
    )

    chunks = split_text(synthetic_doc, document_id="doc-huangshan")
    print(f"Parsed document into {len(chunks)} chunks")

    index = InMemoryKnowledgeIndex()
    index.add_document("doc-huangshan", metadata, chunks)
    print(f"Index contains {len(index)} document(s)")

    questions = [
        "黄山几点开放？",
        "索道什么时候运行？",
        "门票多少钱？",
        "附近有什么好吃的？",
    ]

    for question in questions:
        response = answer_with_index(question, index)
        print(f"\nQ: {question}")
        print(f"A: {response.answer}")
        print(f"Status: {response.status}")
        if response.citations:
            for citation in response.citations:
                print(f"  Source: {citation.title} ({citation.date})")
        if response.limitations:
            for limitation in response.limitations:
                print(f"  Note: {limitation}")


def demo_vision_pipeline() -> None:
    print("\n" + "=" * 60)
    print("2. VISION COUNTING PIPELINE")
    print("=" * 60)

    # Horizontal virtual line across frame at y=0.5
    # Entry side = "left" (above line in image coords)
    counter = VirtualLineCounter(
        line_start=(0.0, 0.5),
        line_end=(1.0, 0.5),
        entry_side="left",
    )
    tracker = CentroidTracker(max_distance=50)

    # Simulate 6 frames with 2 persons moving across the line
    # Person A: moves from below (y=0.7) to above (y=0.3) → entry
    # Person B: moves from above (y=0.3) to below (y=0.7) → exit
    frames = [
        # frame 0: A below y=340, B above y=60
        [(100, 320, 140, 360), (300, 40, 340, 80)],
        # frame 1: A y=300, B y=100
        [(105, 280, 145, 320), (305, 80, 345, 120)],
        # frame 2: A y=260, B y=140
        [(110, 240, 150, 280), (310, 120, 350, 160)],
        # frame 3: A y=220 (still below), B y=180 (still above)
        [(115, 200, 155, 240), (315, 160, 355, 200)],
        # frame 4: A y=180 (crossed above), B y=220 (crossed below)
        [(120, 160, 160, 200), (320, 200, 360, 240)],
        # frame 5: A y=140, B y=260
        [(125, 120, 165, 160), (325, 240, 365, 280)],
    ]

    for frame_index, detections in enumerate(frames):
        tracks = tracker.update(detections, frame_index=frame_index)
        print(f"\nFrame {frame_index}: {len(tracks)} active tracks")

        for track_id, track in tracks.items():
            cx, cy = track.centroid
            # Normalize to 0-1 assuming 640x400 frame
            normalized = (cx / 640.0, cy / 400.0)
            kind = counter.update_track(str(track_id), normalized)
            if kind:
                print(f"  Track {track_id}: {kind.upper()} at {normalized}")

    print(f"\nFinal counts: entries={counter.in_count}, exits={counter.out_count}")

    # Demonstrate manual validation
    timestamp = datetime(2026, 10, 11, 9, 0, tzinfo=UTC)
    manual = [CountWindow(timestamp, entries=2, exits=1)]
    automatic = [CountWindow(timestamp, entries=counter.in_count, exits=counter.out_count)]

    try:
        validation = validate_counts(manual, automatic)
        print(f"Manual validation: sample={validation.sample_count}, "
              f"entry_MAE={validation.entries_mae}, exit_MAE={validation.exits_mae}")
    except ValueError as exc:
        print(f"Validation skipped: {exc}")


def demo_forecast_pipeline() -> None:
    print("\n" + "=" * 60)
    print("3. SHORT-TERM FORECAST PIPELINE")
    print("=" * 60)

    tz = timezone(timedelta(hours=8))
    cutoff = datetime(2026, 10, 11, 10, 0, tzinfo=tz)

    # Synthetic 5-minute interval entry counts (12 history points)
    base_counts = [5, 7, 8, 10, 12, 15, 14, 16, 18, 17, 19, 20]
    history = [
        (cutoff - timedelta(minutes=5 * (len(base_counts) - i)), float(count))
        for i, count in enumerate(base_counts)
    ]

    print(f"History: {len(history)} points at 5-min intervals")
    print(f"Values: {base_counts}")

    # Walk-forward backtest
    backtest = walk_forward_persistence(base_counts, minimum_train=4)
    print("\nWalk-forward backtest:")
    print(f"  Samples: {backtest['sample_count']:.0f}")
    print(f"  MAE: {backtest['mae']:.3f}")
    print(f"  sMAPE: {backtest['smape']:.3f}")

    # Generate 30-min forecast
    points, validation = forecast_from_history(
        history=history,
        cutoff=cutoff,
        horizon_minutes=30,
        step_minutes=5,
    )

    print(f"\n30-minute forecast ({len(points)} points):")
    for point in points:
        print(f"  {point.target_time.strftime('%H:%M')} "
              f"value={point.value:.1f} "
              f"range=[{point.lower:.1f}, {point.upper:.1f}]")

    print(f"\nValidation MAE: {validation['mae']:.3f}")


def main() -> None:
    print("E MODULE END-TO-END DEMO (SYNTHETIC DATA)")
    print("No real documents, videos, or models required.\n")

    demo_knowledge_pipeline()
    demo_vision_pipeline()
    demo_forecast_pipeline()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nAll pipelines run successfully with synthetic data.")
    print("Real results require C-provided documents, authorized videos,")
    print("manual annotations, and count history.")


if __name__ == "__main__":
    main()
