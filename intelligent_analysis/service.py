"""Stable E 0.5 services; D owns jobs, authorization and persistence."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from .agent.metric_tools import run_metric_query
from .agent.orchestrator import answer_with_index
from .contracts import Citation, CountsResponse, DocumentMetadata, JobAccepted, VideoAnalysisConfig
from .integration import DependencyUnavailable, UnsupportedAnalysis, get_bindings, submit
from .knowledge.chunk import split_text
from .knowledge.index import InMemoryKnowledgeIndex
from .knowledge.parse import read_document
from .short_forecast.baseline import forecast_visible_history

MODULE_VERSION = "0.6.0"
MODEL_VERSION = "visible-damped-holt-0.5.0"
_global_index = InMemoryKnowledgeIndex()


def health() -> dict[str, str]:
    return {"module": "intelligent_analysis", "version": MODULE_VERSION, "status": "ready"}


def answer_message(message: str, conversation_id: UUID | None = None,
                   context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    if "metric_query" in context:
        result = run_metric_query(context["metric_query"], context.get("metric_tool"))
        if result.get("status") == "metric_tool_unavailable":
            return {"conversation_id": str(conversation_id or uuid4()),
                    "answer": "指标查询服务尚未接入，无法核实数值。",
                    "status": "metric_tool_unavailable", "citations": [],
                    "used_metric_queries": [], "limitations": []}
        required = {"metric", "value", "source_ids", "period_start", "period_end", "queried_at"}
        if not required.issubset(result) or not result["source_ids"]:
            raise ValueError("Metric tool result must include time, metric and source provenance")
        return {"conversation_id": str(conversation_id or uuid4()), "status": "answered",
                "answer": f"{result['metric']}：{result['value']}（{result['period_start']}—{result['period_end']}）。",
                "citations": [Citation(type="metric", id=str(s), title=result["metric"]).model_dump(mode="json")
                              for s in result["source_ids"]],
                "used_metric_queries": [str(context["metric_query"])],
                "metric_result": result, "limitations": []}
    bindings = get_bindings()
    if bindings.knowledge_snapshot_loader is not None:
        verified_index = InMemoryKnowledgeIndex.from_payload(bindings.knowledge_snapshot_loader())
        return answer_with_index(message, verified_index, conversation_id,
            as_of=context.get("as_of", datetime.now(UTC))).model_dump(mode="json")
    path = bindings.knowledge_index_path
    if path:
        try:
            load_knowledge_index(path)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise DependencyUnavailable("Published knowledge index is unavailable or invalid") from exc
    return answer_with_index(message, _global_index, conversation_id,
                             as_of=context.get("as_of", datetime.now(UTC))).model_dump(mode="json")


def index_document(file_path: str, metadata: dict[str, Any]) -> dict[str, Any]:
    validated = DocumentMetadata.model_validate(metadata)
    if not metadata.get("document_id"):
        raise ValueError("C document_id is required")
    if not metadata.get("document_version"):
        raise ValueError("C document_version is required")
    payload = {"document_id": metadata["document_id"], "file_path": file_path,
               "version": metadata["document_version"],
               "document_version": metadata["document_version"],
               "metadata": validated.model_dump(mode="json")}
    result = submit("knowledge_index", payload)
    return {"document_id": metadata["document_id"], "index_status": "pending",
            "job_id": str(UUID(str(result["job_id"])))}


def process_document_index(file_path: str, metadata: dict[str, Any],
                           document_id: str | None = None) -> dict[str, Any]:
    document_id = document_id or metadata.get("document_id")
    if not document_id:
        raise ValueError("C document_id is required; filenames are not document identities")
    document_metadata = DocumentMetadata.model_validate(metadata)
    chunks = split_text(read_document(file_path), document_id=document_id)
    if not chunks:
        raise ValueError("Document has no extractable text")
    _global_index.add_document(document_id, document_metadata, chunks)
    return {"document_id": document_id, "index_status": "ready", "chunk_count": len(chunks)}


def reindex_documents(document_ids: list[str], reason: str) -> dict[str, Any]:
    if not 1 <= len(document_ids) <= 100 or not reason.strip():
        raise ValueError("1—100 document IDs and a reason are required")
    result = submit("knowledge_reindex", {"document_ids": document_ids, "reason": reason})
    return {"job_id": str(UUID(str(result["job_id"]))), "pending_count": len(document_ids)}


def save_knowledge_index(path: str) -> None:
    _global_index.save(path)


def load_knowledge_index(path: str) -> None:
    global _global_index
    _global_index = InMemoryKnowledgeIndex.load(path)


def analyze_video(video_id: UUID, config: dict[str, Any]) -> dict[str, Any]:
    validated = VideoAnalysisConfig.model_validate(config)
    checker = get_bindings().validate_analysis
    if checker is None:
        raise UnsupportedAnalysis("No validated P2PNet weights/runtime configured")
    checker(validated.model_dump(mode="json", exclude_none=True))
    result = submit("video_analysis", {"video_id": str(video_id),
                                      "config": validated.model_dump(mode="json", exclude_none=True)})
    accepted = JobAccepted(job_id=result["job_id"], analysis_id=result["analysis_id"],
                           inference_engine=validated.inference_engine)
    return {**accepted.model_dump(mode="json"), "video_id": str(video_id),
            "count_metric": "camera_visible_people"}


def get_camera_counts(video_id: UUID, analysis_id: UUID, start: str | None = None,
                      end: str | None = None, grain: str = "5min") -> dict[str, Any]:
    if grain not in {"frame", "5min"}:
        raise ValueError("grain must be frame or 5min")
    start_at = _aware(start) if start else None
    end_at = _aware(end) if end else None
    if start_at and end_at and start_at >= end_at:
        raise ValueError("start must precede end")
    reader = get_bindings().load_counts
    if reader is None:
        raise DependencyUnavailable("D load_counts binding is required")
    raw = reader(str(video_id), str(analysis_id))
    if any("entries" in p or "exits" in p for p in raw.get("points", [])):
        raise UnsupportedAnalysis("Legacy entries/exits are not visible people")
    if raw.get("analysis") and raw["analysis"].get("count_model") != "p2pnet":
        raise UnsupportedAnalysis("Stored analysis uses a retired count model; rebuild as P2PNet")
    response = CountsResponse.model_validate(raw)
    if response.video_id != video_id or response.analysis_id != analysis_id:
        raise ValueError("Count result does not belong to requested video/analysis")
    response.points = [p for p in response.points if p.grain == grain
                       and (start_at is None or (p.recorded_at or p.period_start) >= start_at)
                       and (end_at is None or (p.recorded_at or p.period_end) <= end_at)]
    return response.model_dump(mode="json", exclude_none=False)


def forecast_short_term(video_id: UUID, analysis_id: UUID, cutoff_at: str,
                        horizon_minutes: int, step_minutes: int = 5) -> dict[str, Any]:
    if type(horizon_minutes) is not int or horizon_minutes not in (15, 30, 60):
        raise ValueError("horizon_minutes must be 15, 30 or 60")
    if type(step_minutes) is not int or step_minutes != 5:
        raise ValueError("step_minutes must be 5")
    cutoff = _aware(cutoff_at)
    counts = get_camera_counts(video_id, analysis_id, end=cutoff_at, grain="5min")
    if counts["status"] != "ready":
        return {"metric": "camera_visible_people", "status": "data_insufficient",
                "forecast_points": [], "model_version": MODEL_VERSION,
                "reason": "Analysis is not ready"}
    if not counts["recorded_start_at"] or not counts["recorded_end_at"]:
        raise DependencyUnavailable("Recording bounds are required for forecast validation")
    if not _aware(counts["recorded_start_at"]) <= cutoff <= _aware(counts["recorded_end_at"]):
        raise ValueError("cutoff_at must lie within recording bounds")
    history = [(_aware(p["period_end"]), p["value"] if p["quality_status"] == "good" else None)
               for p in counts["points"]]
    return forecast_from_count_history(history, cutoff, horizon_minutes, step_minutes)


def forecast_from_count_history(history: list[tuple[Any, float | None]], cutoff_at: Any,
                                horizon_minutes: int, step_minutes: int = 5) -> dict[str, Any]:
    cutoff = _aware(cutoff_at) if isinstance(cutoff_at, str) else cutoff_at
    return forecast_visible_history(history, cutoff, horizon_minutes, step_minutes)


def _aware(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value)
    if timestamp.utcoffset() is None:
        raise ValueError("timezone-aware timestamp required")
    return timestamp
