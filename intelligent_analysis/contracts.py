"""Pydantic contracts shared by service-level functions."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

QualityStatus = Literal["good", "degraded", "unavailable"]
ForecastStatus = Literal["ready", "data_insufficient", "quality_insufficient"]
Direction = Literal["entries", "exits"]
Device = Literal["CPU", "GPU", "NPU", "AUTO"]
EntrySide = Literal["left", "right"]
IndexStatus = Literal["pending", "ready", "failed"]


class Citation(BaseModel):
    type: Literal["document", "metric", "event"]
    id: str
    title: str
    url: str | None = None
    date: datetime | None = None
    chunk_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: UUID
    answer: str
    status: Literal["answered", "insufficient_evidence"]
    citations: list[Citation] = Field(default_factory=list)
    used_metric_queries: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class DocumentMetadata(BaseModel):
    title: str
    publisher: str
    source_url: str | None = None
    published_at: datetime | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    permission_note: str


class TextChunk(BaseModel):
    chunk_id: str
    document_id: str
    order: int
    text: str


class IndexAccepted(BaseModel):
    document_id: str
    index_status: Literal["pending"] = "pending"
    job_id: UUID = Field(default_factory=uuid4)


class ReindexAccepted(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    pending_count: int = Field(ge=1)


class CountLine(BaseModel):
    x1: float = Field(ge=0, le=1)
    y1: float = Field(ge=0, le=1)
    x2: float = Field(ge=0, le=1)
    y2: float = Field(ge=0, le=1)


class VideoAnalysisConfig(BaseModel):
    detector_model_version: str
    openvino_version: str
    device: Device
    count_line: CountLine
    entry_side: EntrySide
    interval_minutes: Literal[1, 5, 15]
    tracker_config_id: str | None = None


class JobAccepted(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    analysis_id: UUID = Field(default_factory=uuid4)
    status: Literal["queued"] = "queued"
    inference_engine: Literal["openvino"] = "openvino"


class CountPoint(BaseModel):
    window_start: datetime
    window_end: datetime
    entries: int = Field(ge=0)
    exits: int = Field(ge=0)
    quality_status: QualityStatus
    detector_model_version: str
    openvino_version: str
    device: Device


class ManualValidation(BaseModel):
    sample_count: int = Field(ge=0)
    mae: float = Field(ge=0)


class CountsResponse(BaseModel):
    analysis_id: UUID
    status: Literal["ready", "analysis_not_ready"]
    points: list[CountPoint] = Field(default_factory=list)
    manual_validation: ManualValidation | None = None


class ForecastPoint(BaseModel):
    target_time: datetime
    value: float = Field(ge=0)
    lower: float = Field(ge=0)
    upper: float = Field(ge=0)


class ForecastResponse(BaseModel):
    status: ForecastStatus
    forecast_points: list[ForecastPoint] = Field(default_factory=list)
    training_cutoff: datetime | None = None
    model_version: str
    validation_error: float | None = None
    reason: str | None = None
