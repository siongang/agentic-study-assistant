"""Study plan models (Phase 8)."""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ExamInfo(BaseModel):
    """Information about an exam in the plan."""
    exam_id: str
    exam_name: str
    exam_date: Optional[str] = None
    course: str = Field(default="", description="Course code (e.g., HLTH 204)")
    source_file_id: str = ""


class PracticeProblemRef(BaseModel):
    """Reference to a practice problem."""
    text: str
    page: int


class StudyBlock(BaseModel):
    """A single study block for a topic."""
    exam_id: str
    exam_name: str
    course: str
    chapter: int
    chapter_title: str
    topic: str  # The bullet text
    objective: str  # Same as topic, but formatted
    reading_pages: str = Field(default="", description="e.g., 'Triola, pp. 21-27, 31-32'")
    practice_problems: list[PracticeProblemRef] = Field(default_factory=list)
    key_terms: list[str] = Field(default_factory=list)
    study_question: str = Field(default="", description="Question based on textbook content")
    time_estimate_minutes: int = Field(default=30, ge=0)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: str = Field(default="", description="Warnings or special instructions")


class StudyDay(BaseModel):
    """Study schedule for a single day."""
    date: str  # ISO format YYYY-MM-DD
    day_name: str  # e.g., "Monday"
    total_minutes: int = 0
    blocks: list[StudyBlock] = Field(default_factory=list)
    
    def add_block(self, block: StudyBlock):
        """Add a block and update total minutes."""
        self.blocks.append(block)
        self.total_minutes += block.time_estimate_minutes


class StudyPlan(BaseModel):
    """Complete multi-exam study plan."""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    exams: list[ExamInfo] = Field(default_factory=list)
    total_days: int = 0
    total_study_hours: float = 0.0
    strategy: str = Field(default="balanced", description="Scheduling strategy used")
    days: list[StudyDay] = Field(default_factory=list)
    
    # Planning metadata
    start_date: str = ""
    end_date: str = ""
    minutes_per_day: int = 90
    total_topics: int = 0
    
    def calculate_totals(self):
        """Calculate total days, hours, and topics."""
        self.total_days = len(self.days)
        total_minutes = sum(day.total_minutes for day in self.days)
        self.total_study_hours = total_minutes / 60.0
        self.total_topics = sum(len(day.blocks) for day in self.days)
    
    def get_exam_stats(self) -> dict[str, dict]:
        """Get per-exam statistics."""
        stats = {}
        for exam in self.exams:
            exam_blocks = [
                block for day in self.days 
                for block in day.blocks 
                if block.exam_id == exam.exam_id
            ]
            stats[exam.exam_id] = {
                "exam_name": exam.exam_name,
                "topics": len(exam_blocks),
                "total_minutes": sum(b.time_estimate_minutes for b in exam_blocks),
                "avg_confidence": sum(b.confidence_score for b in exam_blocks) / len(exam_blocks) if exam_blocks else 0.0
            }
        return stats
