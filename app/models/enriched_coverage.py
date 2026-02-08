"""Enriched coverage models with textbook evidence (Phase 7)."""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ReadingPages(BaseModel):
    """Page ranges for reading material."""
    file_id: str
    filename: str
    page_ranges: list[list[int]] = Field(
        default_factory=list,
        description="List of consolidated page ranges [[start, end], ...]"
    )


class PracticeProblem(BaseModel):
    """A practice problem reference."""
    file_id: str
    filename: str
    page: int
    snippet: str = Field(description="First ~100 chars of the problem text")


class EnrichedTopic(BaseModel):
    """Topic enriched with textbook evidence via RAG."""
    chapter: int
    chapter_title: str
    bullet: str
    reading_pages: ReadingPages
    practice_problems: list[PracticeProblem] = Field(default_factory=list)
    key_terms: list[str] = Field(default_factory=list)
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Average retrieval score (0-1)"
    )
    chunks_retrieved: int = Field(default=0, description="Number of chunks found")
    notes: str = Field(default="", description="Any warnings or issues")
    # Store top chunk snippets for question generation
    top_chunks: list[str] = Field(default_factory=list, description="Top 2-3 chunk excerpts")


class EnrichedCoverage(BaseModel):
    """Exam coverage enriched with concrete textbook evidence."""
    exam_id: str
    exam_name: str
    exam_date: Optional[str] = None
    source_file_id: str
    enriched_at: datetime = Field(default_factory=datetime.now)
    topics: list[EnrichedTopic] = Field(default_factory=list)
    
    # Enrichment statistics
    total_topics: int = 0
    high_confidence_count: int = 0  # >= 0.75
    medium_confidence_count: int = 0  # 0.6 - 0.75
    low_confidence_count: int = 0  # < 0.6
    
    def calculate_stats(self):
        """Calculate enrichment statistics."""
        self.total_topics = len(self.topics)
        self.high_confidence_count = sum(1 for t in self.topics if t.confidence_score >= 0.75)
        self.medium_confidence_count = sum(1 for t in self.topics if 0.6 <= t.confidence_score < 0.75)
        self.low_confidence_count = sum(1 for t in self.topics if t.confidence_score < 0.6)
