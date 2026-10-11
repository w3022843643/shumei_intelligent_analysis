"""Parse authorized text and Markdown documents."""

from __future__ import annotations

from pathlib import Path


class UnsupportedDocumentError(ValueError):
    """Raised when a document type is not supported by the minimal parser."""


def read_text_file(file_path: str | Path) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix not in {".txt", ".md", ".markdown"}:
        raise UnsupportedDocumentError(f"Unsupported document type: {suffix}")
    return path.read_text(encoding="utf-8")
