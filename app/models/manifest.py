"""Manifest of ingested documents and index state (Phase 1)."""
from pydantic import BaseModel, Field
from typing import Literal


class ManifestFile(BaseModel):
    """Single file entry in the manifest."""
    file_id: str  # stable internal id, keep if unchanged
    path: str  # relative path from storage/uploads/
    filename: str
    sha256: str
    size_bytes: int
    modified_time: float  # unix timestamp
    doc_type: str = "unknown"
    status: Literal["new", "processed", "stale", "error"] = "new"
    derived: list[str] = Field(default_factory=list)  # derived artifact paths
    error: str | None = None  # optional error message for status="error"
    # Phase 3: classification metadata
    doc_confidence: float | None = None  # 0.0-1.0 confidence score
    doc_reasoning: str | None = None  # LLM reasoning for classification


class Manifest(BaseModel):
    """State of uploads and indexing."""
    version: int = 1
    last_scan: str  # ISO timestamp
    files: list[ManifestFile] = Field(default_factory=list)
